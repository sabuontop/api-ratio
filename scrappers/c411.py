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

COOKIES_FILE = "c411_cookies.json"
LOGIN_PAGE_URL = "https://c411.org/login"
USER_STATS_URL = "https://c411.org/api/auth/me"

async def _get_c411_cookies(ctx: BrowserContext, page: Page) -> bool:
    """Automated login to get fresh C411 cookies if missing or expired"""
    user, psw = os.getenv("C411_USER"), os.getenv("C411_PASS")
    if not (user and psw): 
        raise MissingCredentialsError("Missing C411 Username or Password")
    

    try:
        logger.info("C411: Attempting automated login...")
        await page.goto(LOGIN_PAGE_URL)
        await page.fill('input[placeholder*="Pseudo"]', user)
        await page.fill('input[placeholder*="Mot de passe"]', psw)
        await asyncio.sleep(1)
        
        login_btn = await page.query_selector('button:has-text("Connexion"), button.bg-emerald-500')
        if login_btn:
            await login_btn.click()
        else:
            await page.keyboard.press("Enter")
        
        await asyncio.sleep(5) 
        
        await page.goto(USER_STATS_URL)
        content = await page.inner_text("body")
        api_data = json.loads(content)
        
        if api_data.get("authenticated"):
            cookies = await ctx.cookies()
            write_file(COOKIES_FILE, json.dumps(cookies))
            logger.info("C411: New cookies obtained and saved.")
            return True
    except Exception as e:
            logger.error(f"C411 Login failed: {e}")

    return False
  
  
async def get_stats(headless: bool = True) -> Dict[str, Any]:
  async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent=default_user_agent)
        page = await context.new_page()
        try:
            res : Dict[str, Any] = {"raw_upload": 0, "raw_download": 0}
            try:
                cookies = load_file(COOKIES_FILE, is_json=True)
            except FileNotFoundError:
                await _get_c411_cookies(context, page)
                cookies = load_file(COOKIES_FILE, is_json=True)

            await context.add_cookies(cookies)
            response = await context.request.get(USER_STATS_URL)
            api_data = await response.json() if response.ok else {}
            if not api_data.get("authenticated"):
                logger.warning("C411: Session expired or missing, logging in...")
                if await _get_c411_cookies(context, page):
                    cookies = load_file(COOKIES_FILE, is_json=True)
                    await context.add_cookies(cookies)
                    response = await context.request.get(USER_STATS_URL)
                    api_data = await response.json() if response.ok else {}
                else:
                    raise ScrappingError("C411: Failed to authenticate")

            user_data = api_data.get("user")
            if user_data:
                up = user_data.get("uploaded", 0)
                dl = user_data.get("downloaded", 0)
                res["raw_upload"] = up
                res["raw_download"] = dl
                res["bonus"] = 0 # No bonus system on C411

            return res
        except (MissingCredentialsError, ScrappingError) as e:
            raise e
        except Exception as e:
            raise ScrappingError(e)
        finally:
            await browser.close()