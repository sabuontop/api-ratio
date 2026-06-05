from __future__ import annotations

import os
import re
from typing import Any, Dict, Tuple

import httpx
from bs4 import BeautifulSoup

from util import default_user_agent, parse_bytes

BASE = "https://hd-space.org"
HOME_PATH = "/index.php"

def _load_cookies() -> Tuple[Dict[str, str], str]:
    """Return (cookies_dict, uid). Raises RuntimeError if env var is missing or malformed."""
    header = os.getenv("HDSPACE_COOKIE", "").strip().strip('"').strip("'")
    if not header:
        raise RuntimeError(
            "HDSPACE_COOKIE is not set. Log into hd-space.org, "
            "copy the cookies from DevTools → Application → Cookies "
            "(uid and pass), and set HDSPACE_COOKIE='uid=...; pass=...' in .env."
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
            "HDSPACE_COOKIE is missing required cookies. "
            "Both 'uid' and 'pass' are needed."
        )
    return cookies, cookies["uid"]

def _looks_like_login_page(html: str) -> bool:
    return '<td class="lista" align="center"><input type="submit" value="Login"' in html and 'want_username1' in html and 'want_password1' in html

def _parse_toolbar_stats(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    
    up_td   = soup.find("td", class_="green", string=re.compile(r"UP:", re.I))
    dl_td   = soup.find("td", class_="red",   string=re.compile(r"DL:", re.I))
    ratio_td = soup.find("td", class_="yellow", string=re.compile(r"Ratio:", re.I))
    bonus_a  = soup.find("a", href=re.compile(r"seedbonus"))

    def extract(tag, pattern):
        if not tag:
            return ""
        m = re.search(pattern, tag.get_text(strip=True), re.I)
        return m.group(1) if m else ""

    return {
        "raw_upload":   parse_bytes(extract(up_td,    r"UP:\s*(.+)")),
        "raw_download": parse_bytes(extract(dl_td,    r"DL:\s*(.+)")),
        "ratio":        float(extract(ratio_td,       r"Ratio:\s*([0-9.]+)") or 0),
        "bonus":        float(extract(bonus_a, r"Bonus:\s*([0-9,\.]+)").replace(",", "") or 0),
    }

async def get_stats(_: bool) -> Dict[str, Any]:
    """
    Fetch HD-Space stats. `headless` is accepted for API compatibility
    with browser-based scrapers but ignored — this one is pure HTTP.
    """
    cookies, _ = _load_cookies()

    headers = {
        "User-Agent": default_user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Referer": BASE + "/",
    }

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        home_resp = await client.get(
            BASE + HOME_PATH,
            cookies=cookies,
            headers=headers,
        )
        if _looks_like_login_page(home_resp.text) or "account-login" in str(home_resp.url).lower():
            raise RuntimeError(
                "Session expired or cookies invalid. Re-export HDSPACE_COOKIE "
                "from your browser."
            )

    return _parse_toolbar_stats(home_resp.text)
