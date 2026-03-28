import asyncio
import os
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv

from util import default_user_agent, load_file, write_file, MissingCredentialsError, ScrappingError

load_dotenv()
logger = logging.getLogger()

TOKEN_FILE = "torr9_token.txt"
LOGIN_PAGE_URL = "https://torr9.net/login"
USER_STATS_URL = "https://api.torr9.net/api/v1/users/me"

async def _get_torr9_token(page: Page) -> Optional[str]:
    """Automated login to get a fresh Torr9 token if missing or expired"""
    user = os.getenv("TORR9_USER") or os.getenv("TOR9_USER")
    psw = os.getenv("TORR9_PASSWORD") or os.getenv("TORR9_PASS") or os.getenv("TOR9_PASS")
    
    if not (user and psw):
        raise MissingCredentialsError("Missing Torr9 Username or Password")
    

    try:
        logger.info("Torr9: Attempting automated login...")
        await page.goto(LOGIN_PAGE_URL)
        await page.fill('input[placeholder*="utilisateur"]', user)
        await page.fill('input[placeholder*="mot de passe"]', psw)
        await asyncio.sleep(1)
        
        btn = await page.query_selector('button:has-text("Se connecter")')
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")
        
        await page.wait_for_load_state("networkidle", timeout=15000)
        
        for _ in range(10):
            token = await page.evaluate("() => localStorage.getItem('token')")
            if token:
                write_file(TOKEN_FILE, token)
                logger.info("Torr9: New token obtained and saved.")
                return token
            await asyncio.sleep(1)
        
        logger.error("Torr9: Login appeared successful but no token found in localStorage.")
    except Exception as e:
        logger.error(f"Torr9 Login failed: {e}")
    return None
  
async def get_stats(headless: bool = True) -> Dict[str, Any]:
  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=headless)
    context = await browser.new_context(user_agent=default_user_agent)
    page = await context.new_page()
    try:
        res : Dict[str, Any] = {"raw_upload": 0, "raw_download": 0}
        token = None
        try:
            token= load_file(TOKEN_FILE).strip()
        except FileNotFoundError:
            token = await _get_torr9_token(page)
        
        if not token:
            raise MissingCredentialsError("Fauked ")
        
        response = await context.request.get(
            USER_STATS_URL,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status == 401:
            logger.warning("Torr9: Token expired, refreshing...")
            token = await _get_torr9_token(page)
            if token:
                response = await context.request.get(
                    USER_STATS_URL,
                    headers={"Authorization": f"Bearer {token}"}
                )
        
        if not response.ok:
            raise ScrappingError(f" Torr9: API Error {response.status}")
        
        api_data = await response.json()
        up = api_data.get("total_uploaded_bytes", 0)
        dl = api_data.get("total_downloaded_bytes", 0)
        res["raw_upload"] = up
        res["raw_download"] = dl

        return res
    except (MissingCredentialsError, ScrappingError) as e:
        raise e
    except Exception as e:
        raise ScrappingError(e)
    finally:
        await browser.close()