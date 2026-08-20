import logging
import os
import re
from typing import Any, Dict

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from util import (
    MissingCredentialsError,
    ScrappingError,
    default_user_agent,
    parse_bytes,
)

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://www.yggreborn.org"
ACCOUNT_URL = "https://www.yggreborn.org/account"


def _parse_html_stats(html: str) -> Dict[str, float]:
    soup = BeautifulSoup(html, "html.parser")
    res = {"raw_upload": 0.0, "raw_download": 0.0, "bonus": 0.0}

    text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if l == "Upload" and i > 0:
            res["raw_upload"] = parse_bytes(lines[i - 1])
        elif l == "Download" and i > 0:
            res["raw_download"] = parse_bytes(lines[i - 1])
        elif ("bonus" in l.lower() or "points" in l.lower()) and i > 0:
            m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", lines[i - 1])
            if m:
                res["bonus"] = float(m.group(1).replace(",", "."))

    if res["raw_upload"] > 0 or res["raw_download"] > 0:
        return res

    infobar = soup.find("div", id="infobar")
    if infobar:
        fonts = infobar.find_all("font")
        if len(fonts) >= 2:
            download_str = fonts[0].get_text(strip=True)
            upload_str = fonts[1].get_text(strip=True)
            res["raw_upload"] = parse_bytes(upload_str)
            res["raw_download"] = parse_bytes(download_str)
            return res

    up_m = re.search(
        r"(?:upload|partage|envoy[eé])\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?\s*[kKmMgGtTpPoO]?[iI]?[bB]?)",
        html,
        re.I,
    )
    dl_m = re.search(
        r"(?:download|t[eé]l[eé]charg[eé])\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?\s*[kKmMgGtTpP]?[iI]?[bB]?)",
        html,
        re.I,
    )
    bonus_m = re.search(
        r"(?:bonus|points?|cr[ée]dit)\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?)", html, re.I
    )

    if up_m:
        res["raw_upload"] = parse_bytes(up_m.group(1))
    if dl_m:
        res["raw_download"] = parse_bytes(dl_m.group(1))
    if bonus_m:
        res["bonus"] = float(bonus_m.group(1).replace(",", "."))

    return res


async def get_stats(headless: bool = True) -> Dict[str, Any]:
    cookie_str = os.getenv("YGGREBORN_COOKIE", "").strip().strip('"').strip("'")
    user_agent = os.getenv("YGGREBORN_USER_AGENT", "").strip() or default_user_agent

    if not cookie_str:
        raise MissingCredentialsError(
            "YGG Reborn requires session cookies (Cloudflare protection active). "
            "Log into www.yggreborn.org in your browser, copy cookies from "
            "DevTools → Application → Cookies (cf_clearance, __ygg_sess), "
            "and set YGGREBORN_COOKIE='...' in your .env file."
        )

    cookies: Dict[str, str] = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            name, value = name.strip(), value.strip()
            if name and value:
                cookies[name] = value

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr,fr-FR;q=0.9,en-US;q=0.5,en;q=0.3",
        "Referer": BASE_URL + "/",
    }

    try:
        async with httpx.AsyncClient(
            cookies=cookies,
            headers=headers,
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            resp = await client.get(ACCOUNT_URL)
            if (
                "login" in str(resp.url).lower()
                or "just a moment" in resp.text.lower()
                or "cf-turnstile" in resp.text.lower()
            ):
                raise ScrappingError(
                    "YGG Reborn Cloudflare validation failed (HTTP 403). "
                    "Make sure your YGGREBORN_COOKIE is valid and set YGGREBORN_USER_AGENT "
                    "to match your browser's User-Agent in .env."
                )

            return _parse_html_stats(resp.text)
    except (MissingCredentialsError, ScrappingError) as e:
        raise e
    except Exception as e:
        raise ScrappingError(f"YGG Reborn Scrapping error: {e}")
