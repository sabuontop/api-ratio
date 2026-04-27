import asyncio
import os
import json
import logging
from typing import Dict, Any
from playwright.async_api import async_playwright, BrowserContext, Page
from dotenv import load_dotenv

from util import default_user_agent, load_file, write_file, MissingCredentialsError, ScrappingError

load_dotenv()
logger = logging.getLogger()

COOKIES_FILE = "lacale_cookies.json"
LOGIN_PAGE_URL = "https://la-cale.space/login"
USER_STATS_URL = "https://la-cale.space/api/internal/me"


async def _get_lacale_cookies(ctx: BrowserContext, page: Page) -> bool:
    """Navigate login page with Playwright to bypass anti-bot, handle optional 2FA, then save session cookies"""
    email = os.getenv("LACALE_USER")
    password = os.getenv("LACALE_PASS")
    if not (email and password):
        raise MissingCredentialsError("Missing La Cale email or password")

    try:
        logger.info("La Cale: Attempting automated login...")
        await page.goto(LOGIN_PAGE_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        await page.fill('input[type="email"], input[name="email"], input[placeholder*="mail"]', email)
        await page.fill('input[type="password"], input[name="password"], input[placeholder*="assword"]', password)
        await asyncio.sleep(1)

        btn = await page.query_selector('button[type="submit"], button:has-text("Connexion"), button:has-text("Se connecter")')
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

        await asyncio.sleep(4)

        # Validate session by calling /me
        response = await ctx.request.get(USER_STATS_URL)
        if response.ok:
            api_data = await response.json()
            if api_data.get("id"):
                cookies = await ctx.cookies()
                write_file(COOKIES_FILE, json.dumps(cookies))
                logger.info(f"La Cale: Login successful as {api_data.get('username')}, cookies saved.")
                return True
            logger.error(f"La Cale: Login response unexpected: {api_data}")
        else:
            logger.error(f"La Cale: /me returned {response.status} after login")
    except Exception as e:
        logger.error(f"La Cale: Login failed: {e}")

    return False


async def get_stats(headless: bool = True) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent=default_user_agent)
        page = await context.new_page()
        try:
            res: Dict[str, Any] = {"raw_upload": 0, "raw_download": 0}

            try:
                cookies = load_file(COOKIES_FILE, is_json=True)
            except FileNotFoundError:
                await _get_lacale_cookies(context, page)
                cookies = load_file(COOKIES_FILE, is_json=True)

            await context.add_cookies(cookies)
            response = await context.request.get(USER_STATS_URL)
            api_data = await response.json() if response.ok else {}

            if not api_data.get("id"):
                logger.warning("La Cale: Session expired or invalid, re-logging in...")
                if await _get_lacale_cookies(context, page):
                    cookies = load_file(COOKIES_FILE, is_json=True)
                    await context.add_cookies(cookies)
                    response = await context.request.get(USER_STATS_URL)
                    api_data = await response.json() if response.ok else {}
                else:
                    raise ScrappingError("La Cale: Failed to authenticate")

            res["raw_upload"] = float(api_data.get("uploaded", 0))
            res["raw_download"] = float(api_data.get("downloaded", 0))
            res["bonus"] = float(api_data.get("bonusPoints", 0))
            return res

        except (MissingCredentialsError, ScrappingError) as e:
            raise e
        except Exception as e:
            raise ScrappingError(e)
        finally:
            await browser.close()
