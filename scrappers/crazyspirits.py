"""
CrazySpirits scraper (cookie-based auth).

Login is blocked by an anti-bot layer, so we skip it: the user logs in with
their own browser, copies the session cookies, and exports them via the
CRAZYSPIRITS_COOKIE env var. We reuse them over plain HTTP.

Expected env var format (raw "Cookie:" header, from DevTools → Application → Cookies):
    CRAZYSPIRITS_COOKIE=uid=323; pass=2511f465ab31298e937198acb707b22ed911dbd4

Bonus is read from /index.php (homepage); ratio / upload / download are
read from /account-details.php?id=<uid>.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Tuple

import httpx
from bs4 import BeautifulSoup

from util import default_user_agent, parse_bytes

BASE = "https://crazyspirits.com"
HOME_PATH = "/index.php"
ACCOUNT_PATH = "/account-details.php?id={uid}"


# --- Cookie loading --------------------------------------------------------

def _load_cookies() -> Tuple[Dict[str, str], str]:
    """Return (cookies_dict, uid). Raises RuntimeError if env var is missing or malformed."""
    header = os.getenv("CRAZYSPIRITS_COOKIE", "").strip().strip('"').strip("'")
    if not header:
        raise RuntimeError(
            "CRAZYSPIRITS_COOKIE is not set. Log into crazyspirits.com, "
            "copy the cookies from DevTools → Application → Cookies "
            "(uid and pass), and set CRAZYSPIRITS_COOKIE='uid=...; pass=...' in .env."
        )

    cookies: Dict[str, str] = {}
    for part in header.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        name, _, value = part.partition("=")
        name, value = name.strip(), value.strip()
        if name and value:
            cookies[name] = value

    if "uid" not in cookies or "pass" not in cookies:
        raise RuntimeError(
            "CRAZYSPIRITS_COOKIE is missing required cookies. "
            "Both 'uid' and 'pass' are needed."
        )
    return cookies, cookies["uid"]


# --- Parsing ---------------------------------------------------------------

def _looks_like_login_page(html: str) -> bool:
    text = html.lower()
    return "connexion" in text and 'name="username"' in text and 'name="password"' in text


_BONUS_RE = re.compile(r"(?:bonus|points?|cr[ée]dit)\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?)", re.I)


def _parse_bonus(html: str) -> float:
    """Extract bonus points from the homepage (/index.php)."""
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    m = _BONUS_RE.search(text.replace("\u00a0", " "))
    if not m:
        return 0.0
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return 0.0


def _find_stat(soup: BeautifulSoup, label: str) -> str:
    """
    Find a <td> whose text starts with the given label and return the text of
    its <span class="detail_fix"> child. Returns "" if not found.

    Example HTML:
        <td align="left">Partager: <span class="detail_fix">150 GiB</span>...</td>
    """
    label_lower = label.lower()
    for td in soup.find_all("td"):
        td_text = td.get_text(" ", strip=True).lower()
        if td_text.startswith(label_lower):
            span = td.find("span", class_="detail_fix")
            if span:
                return span.get_text(strip=True)
    return ""


def _parse_account_stats(html: str) -> Dict[str, float]:
    """
    Extract raw upload, raw download, and ratio from /account-details.php.

    We use the "Partager" / "Télécharger" pair (the lifetime raw totals that
    match the displayed ratio), not the "Total En Partage" / "Total En
    Téléchargement" pair (which are current active-seed totals).
    """
    soup = BeautifulSoup(html, "html.parser")

    upload_str = _find_stat(soup, "Partager:")
    download_str = _find_stat(soup, "Télécharger:")

    return {
        "raw_upload": parse_bytes(upload_str),
        "raw_download": parse_bytes(download_str),
    }


# --- Entry point (api-ratio contract) --------------------------------------

async def get_stats(headless: bool = True) -> Dict[str, Any]:
    """
    Fetch CrazySpirits stats. `headless` is accepted for API compatibility
    with browser-based scrapers but ignored — this one is pure HTTP.
    """
    cookies, uid = _load_cookies()

    headers = {
        "User-Agent": default_user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Referer": BASE + "/",
    }

    async with httpx.AsyncClient(
        cookies=cookies,
        headers=headers,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        home_resp = await client.get(BASE + HOME_PATH)
        if _looks_like_login_page(home_resp.text) or "account-login" in str(home_resp.url).lower():
            raise RuntimeError(
                "Session expired or cookies invalid. Re-export CRAZYSPIRITS_COOKIE "
                "from your browser."
            )

        account_resp = await client.get(BASE + ACCOUNT_PATH.format(uid=uid))

    bonus = _parse_bonus(home_resp.text)
    account_stats = _parse_account_stats(account_resp.text)

    return {
        "raw_upload": account_stats["raw_upload"],
        "raw_download": account_stats["raw_download"],
        "bonus": bonus,
    }
