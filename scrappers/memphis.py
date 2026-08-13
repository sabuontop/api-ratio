import asyncio
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from playwright.async_api import BrowserContext, Page, async_playwright

from util import (
    MissingCredentialsError,
    ScrappingError,
    default_user_agent,
    load_file,
    parse_bytes,
    write_file,
)

load_dotenv()
logger = logging.getLogger(__name__)

COOKIES_FILE = "memphis_cookies.json"
SESSION_STATUS_URL = "https://memphis.fit/api/session/status"


def _extract_stats_from_json(api_data: dict[str, Any]) -> dict[str, float]:
    if not isinstance(api_data, dict):
        raise ScrappingError("Invalid API response format from Memphis")

    me = api_data.get("me") if isinstance(api_data.get("me"), dict) else api_data
    data = me.get("data") if isinstance(me.get("data"), dict) else me

    up = data.get(
        "uploaded_bytes", data.get("uploaded", data.get("total_uploaded_bytes", 0))
    )
    bonus_up = data.get("bonus_upload", data.get("bonus_uploaded", 0))

    dl = data.get(
        "downloaded_bytes", data.get("downloaded", data.get("total_downloaded_bytes", 0))
    )
    bonus_dl = data.get("bonus_download", data.get("bonus_downloaded", 0))

    raw_upload = float(up) if isinstance(up, (int, float)) else parse_bytes(str(up))
    raw_upload += (
        float(bonus_up)
        if isinstance(bonus_up, (int, float))
        else parse_bytes(str(bonus_up))
    )

    raw_download = float(dl) if isinstance(dl, (int, float)) else parse_bytes(str(dl))
    raw_download += (
        float(bonus_dl)
        if isinstance(bonus_dl, (int, float))
        else parse_bytes(str(bonus_dl))
    )

    bonus_val = data.get(
        "bonus_points",
        data.get(
            "money",
            data.get(
                "seedbonus", data.get("jeton_balance", data.get("bonus", 0))
            ),
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


async def _get_memphis_cookies(ctx: BrowserContext, page: Page) -> bool:
    user = os.getenv("MEMPHIS_USER") or os.getenv("MEMPHIS_USERNAME")
    psw = os.getenv("MEMPHIS_PASS") or os.getenv("MEMPHIS_PASSWORD")

    if not (user and psw):
        raise MissingCredentialsError("Missing Memphis Username or Password")

    try:
        logger.info("Memphis: Attempting automated login via Playwright...")
        await page.goto("https://memphis.fit", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)

        conn_btn = await page.query_selector('button:has-text("Connexion")')
        if conn_btn:
            await conn_btn.click()
            await asyncio.sleep(1)

        await page.fill('#login-username, input[name="username"], input[name="login"]', user)
        await page.fill('#login-password, input[type="password"]', psw)
        await asyncio.sleep(1)

        submit_btn = await page.query_selector(
            '#login-password ~ button, button[type="submit"]:has-text("Connexion"), button:has-text("Se connecter")'
        )
        if submit_btn:
            await submit_btn.click()
        else:
            await page.keyboard.press("Enter")

        await asyncio.sleep(4)

        response = await ctx.request.get(SESSION_STATUS_URL)
        if response.ok:
            api_data = await response.json()
            if api_data.get("authenticated"):
                cookies = await ctx.cookies()
                write_file(COOKIES_FILE, json.dumps(cookies))
                logger.info("Memphis: Login successful, cookies saved.")
                return True

    except Exception as e:
        logger.error(f"Memphis Login failed: {e}")

    return False


async def get_stats(headless: bool = True) -> dict[str, Any]:
    user = os.getenv("MEMPHIS_USER") or os.getenv("MEMPHIS_USERNAME")
    psw = os.getenv("MEMPHIS_PASS") or os.getenv("MEMPHIS_PASSWORD")
    cookie_str = os.getenv("MEMPHIS_COOKIE")

    if not (user and psw) and not cookie_str:
        raise MissingCredentialsError(
            "Missing Memphis credentials. Set MEMPHIS_USER and MEMPHIS_PASS in .env"
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
                if user and psw:
                    await _get_memphis_cookies(context, page)
                    cookies = load_file(COOKIES_FILE, is_json=True)

            if cookies:
                await context.add_cookies(cookies)

            response = await context.request.get(SESSION_STATUS_URL)
            api_data = None
            if response.ok:
                res_json = await response.json()
                if res_json.get("authenticated"):
                    api_data = res_json

            if not api_data and (user and psw):
                logger.warning("Memphis: Session expired or invalid, attempting re-login...")
                if await _get_memphis_cookies(context, page):
                    cookies = load_file(COOKIES_FILE, is_json=True)
                    await context.add_cookies(cookies)
                    response = await context.request.get(SESSION_STATUS_URL)
                    if response.ok:
                        res_json = await response.json()
                        if res_json.get("authenticated"):
                            api_data = res_json

            if not api_data:
                raise ScrappingError(
                    "Memphis: Unable to authenticate. Check your MEMPHIS_USER and MEMPHIS_PASS in .env"
                )

            return _extract_stats_from_json(api_data)

        except (MissingCredentialsError, ScrappingError) as e:
            raise e
        except Exception as e:
            raise ScrappingError(f"Memphis Scrapping error: {e}")
        finally:
            await browser.close()
