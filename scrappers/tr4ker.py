import asyncio
import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from playwright.async_api import async_playwright, BrowserContext, Page
from dotenv import load_dotenv

from util import (
    default_user_agent,
    load_file,
    write_file,
    parse_bytes,
    MissingCredentialsError,
    ScrappingError,
)

load_dotenv()
logger = logging.getLogger(__name__)

COOKIES_FILE = "tr4ker_cookies.json"
LOGIN_PAGE_URL = "https://tr4ker.net/login"
API_URLS = [
    "https://tr4ker.net/api/me",
    "https://tr4ker.net/api/v1/user",
    "https://tr4ker.net/api/user",
    "https://tr4ker.net/api/v1/users/me",
]


def _extract_stats_from_json(api_data: Dict[str, Any]) -> Dict[str, float]:
    if not isinstance(api_data, dict):
        raise ScrappingError("Invalid API response format from TR4KER")

    data = api_data.get("data") if isinstance(api_data.get("data"), dict) else api_data

    up_val = data.get("uploaded", data.get("total_uploaded_bytes", 0))
    bonus_up_val = data.get("bonus_upload", data.get("bonus_uploaded", 0))

    dl_val = data.get("downloaded", data.get("total_downloaded_bytes", 0))
    bonus_dl_val = data.get("bonus_download", data.get("bonus_downloaded", 0))

    raw_upload = float(up_val) if isinstance(up_val, (int, float)) else parse_bytes(str(up_val))
    raw_upload += float(bonus_up_val) if isinstance(bonus_up_val, (int, float)) else parse_bytes(str(bonus_up_val))

    raw_download = float(dl_val) if isinstance(dl_val, (int, float)) else parse_bytes(str(dl_val))
    raw_download += float(bonus_dl_val) if isinstance(bonus_dl_val, (int, float)) else parse_bytes(str(bonus_dl_val))

    bonus_val = data.get(
        "money",
        data.get(
            "seedbonus",
            data.get("bonus_points", data.get("jeton_balance", data.get("bonus", 0))),
        ),
    )

    try:
        bonus = float(bonus_val)
    except (ValueError, TypeError):
        bonus = 0.0

    return {
        "raw_upload": raw_upload,
        "raw_download": raw_download,
        "bonus": bonus,
    }


def _try_fetch_via_api_token(token: str) -> Optional[Dict[str, float]]:
    headers = {
        "User-Agent": default_user_agent,
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "X-API-Key": token,
    }

    param_names = ["apikey", "api_token", "token"]

    for base_url in API_URLS:
        urls = [base_url] + [f"{base_url}?{p}={token}" for p in param_names]
        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8")
                        api_data = json.loads(content)
                        if api_data and (
                            "uploaded" in api_data
                            or "downloaded" in api_data
                            or "data" in api_data
                        ):
                            logger.info(f"TR4KER: Successfully fetched stats via API endpoint {url}")
                            return _extract_stats_from_json(api_data)
            except urllib.error.HTTPError as e:
                logger.debug(f"TR4KER API endpoint {url} returned HTTP {e.code}")
            except Exception as e:
                logger.debug(f"TR4KER API endpoint {url} error: {e}")

    return None


async def _get_tr4ker_cookies(ctx: BrowserContext, page: Page) -> bool:
    user = os.getenv("TR4KER_USER")
    psw = os.getenv("TR4KER_PASS") or os.getenv("TR4KER_PASSWORD")

    if not (user and psw):
        raise MissingCredentialsError("Missing TR4KER Username or Password")

    try:
        logger.info("TR4KER: Attempting automated login...")
        await page.goto(LOGIN_PAGE_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)

        await page.fill(
            'input[type="email"], input[name="username"], input[name="login"], input[placeholder*="Pseudo"], input[placeholder*="mail"], input[placeholder*="utilisateur"]',
            user,
        )
        await page.fill(
            'input[type="password"], input[name="password"], input[placeholder*="mot de passe"], input[placeholder*="Password"]',
            psw,
        )
        await asyncio.sleep(1)

        btn = await page.query_selector(
            'button[type="submit"], button:has-text("Connexion"), button:has-text("Se connecter")'
        )
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

        await asyncio.sleep(4)

        for api_url in API_URLS:
            try:
                response = await ctx.request.get(api_url)
                if response.ok:
                    api_data = await response.json()
                    if api_data:
                        cookies = await ctx.cookies()
                        write_file(COOKIES_FILE, json.dumps(cookies))
                        logger.info("TR4KER: Login successful, cookies saved.")
                        return True
            except Exception:
                pass

        content = await page.content()
        if "logout" in content.lower() or "déconnexion" in content.lower():
            cookies = await ctx.cookies()
            write_file(COOKIES_FILE, json.dumps(cookies))
            logger.info("TR4KER: Login verified via page content, cookies saved.")
            return True

    except Exception as e:
        logger.error(f"TR4KER Login failed: {e}")

    return False


async def get_stats(headless: bool = True) -> Dict[str, Any]:
    token = os.getenv("TR4KER_TOKEN") or os.getenv("TR4KER_API_KEY")
    if token:
        try:
            stats = _try_fetch_via_api_token(token)
            if stats:
                return stats
        except Exception as e:
            logger.warning(f"TR4KER API token request failed, trying Playwright fallback: {e}")

    user = os.getenv("TR4KER_USER")
    psw = os.getenv("TR4KER_PASS") or os.getenv("TR4KER_PASSWORD")

    if not token and not (user and psw):
        raise MissingCredentialsError(
            "Missing TR4KER credentials. Set TR4KER_TOKEN or (TR4KER_USER and TR4KER_PASS) in .env"
        )

    if not (user and psw):
        raise ScrappingError(
            "TR4KER API token request failed or returned invalid data, and no TR4KER_USER/TR4KER_PASS set for browser login."
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(user_agent=default_user_agent)
        page = await context.new_page()
        try:
            cookies = None
            try:
                cookies = load_file(COOKIES_FILE, is_json=True)
            except FileNotFoundError:
                await _get_tr4ker_cookies(context, page)
                cookies = load_file(COOKIES_FILE, is_json=True)

            if cookies:
                await context.add_cookies(cookies)

            api_data = None
            for api_url in API_URLS:
                try:
                    response = await context.request.get(api_url)
                    if response.ok:
                        api_data = await response.json()
                        if api_data:
                            break
                except Exception:
                    pass

            if not api_data:
                logger.warning("TR4KER: Session expired or invalid, attempting re-login...")
                if await _get_tr4ker_cookies(context, page):
                    cookies = load_file(COOKIES_FILE, is_json=True)
                    await context.add_cookies(cookies)
                    for api_url in API_URLS:
                        try:
                            response = await context.request.get(api_url)
                            if response.ok:
                                api_data = await response.json()
                                if api_data:
                                    break
                        except Exception:
                            pass

            if not api_data:
                raise ScrappingError("TR4KER: Failed to retrieve user stats after login")

            return _extract_stats_from_json(api_data)

        except (MissingCredentialsError, ScrappingError) as e:
            raise e
        except Exception as e:
            raise ScrappingError(f"TR4KER Scrapping error: {e}")
        finally:
            await browser.close()
