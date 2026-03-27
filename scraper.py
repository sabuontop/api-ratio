import asyncio, os, json, logging
from typing import Dict, Any, Tuple, Optional
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("scraper")

def format_bytes(size: float) -> str:
    if size is None or size < 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} EB"

async def get_torr9_token() -> Optional[str]:
    """Automated login to get a fresh Torr9 token if missing or expired"""
    user = os.getenv("TORR9_USER") or os.getenv("TOR9_USER")
    psw = os.getenv("TORR9_PASSWORD") or os.getenv("TORR9_PASS") or os.getenv("TOR9_PASS")
    
    if not (user and psw):
        logger.error("Torr9: Credentials (USER/PASSWORD) missing in .env file!")
        return None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await ctx.new_page()
        try:
            logger.info("Torr9: Attempting automated login...")
            await page.goto("https://torr9.net/login")
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
                    with open("torr9_token.txt", "w") as f:
                        f.write(token)
                    logger.info("Torr9: New token obtained and saved.")
                    return token
                await asyncio.sleep(1)
            
            logger.error("Torr9: Login appeared successful but no token found in localStorage.")
        except Exception as e:
            logger.error(f"Torr9 Login failed: {e}")
        finally:
            await browser.close()
    return None

async def get_c411_cookies() -> bool:
    """Automated login to get fresh C411 cookies if missing or expired"""
    user, psw = os.getenv("C411_USER"), os.getenv("C411_PASS")
    if not (user and psw): return False
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await ctx.new_page()
        try:
            logger.info("C411: Attempting automated login...")
            await page.goto("https://c411.org/login")
            await page.fill('input[placeholder*="Pseudo"]', user)
            await page.fill('input[placeholder*="Mot de passe"]', psw)
            await asyncio.sleep(1)
            
            login_btn = await page.query_selector('button:has-text("Connexion"), button.bg-emerald-500')
            if login_btn:
                await login_btn.click()
            else:
                await page.keyboard.press("Enter")
            
            await asyncio.sleep(5) 
            
            await page.goto("https://c411.org/api/auth/me")
            content = await page.inner_text("body")
            api_data = json.loads(content)
            
            if api_data.get("authenticated"):
                cookies = await ctx.cookies()
                with open("c411_cookies.json", "w") as f:
                    json.dump(cookies, f)
                logger.info("C411: New cookies obtained and saved.")
                return True
        except Exception as e:
            logger.error(f"C411 Login failed: {e}")
        finally:
            await browser.close()
    return False

async def get_stats(site: str, headless: bool = True) -> Dict[str, str]:
    """Scrapes the site and returns a dictionary of stats (ratio, upload, download)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        try:
            res = {"ratio": "N/A", "upload": "N/A", "download": "N/A"}
            
            if site == "torr9":
                token = None
                if os.path.exists("torr9_token.txt"):
                    with open("torr9_token.txt", "r") as f:
                        token = f.read().strip()
                
                if not token:
                    token = await get_torr9_token()
                
                if not token:
                    return {"ratio": "No Token", "upload": "N/A", "download": "N/A"}
                
                response = await context.request.get(
                    "https://api.torr9.net/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status == 401:
                    logger.warning("Torr9: Token expired, refreshing...")
                    token = await get_torr9_token()
                    if token:
                        response = await context.request.get(
                            "https://api.torr9.net/api/v1/users/me",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                
                if not response.ok:
                    return {"ratio": f"API Error {response.status}", "upload": "N/A", "download": "N/A"}
                
                api_data = await response.json()
                up = api_data.get("total_uploaded_bytes", 0)
                dl = api_data.get("total_downloaded_bytes", 0)
                res["upload"] = format_bytes(up)
                res["download"] = format_bytes(dl)
                res["ratio"] = f"{up / dl:.2f}" if dl > 0 else "∞" if up > 0 else "0.00"

            elif site == "c411":
                cookie_path = "c411_cookies.json"
                if not os.path.exists(cookie_path):
                    await get_c411_cookies()
                
                if os.path.exists(cookie_path):
                    with open(cookie_path, 'r') as f:
                        cookies = json.load(f)
                        await context.add_cookies(cookies)
                
                response = await context.request.get("https://c411.org/api/auth/me")
                api_data = await response.json() if response.ok else {}
                
                if not api_data.get("authenticated"):
                    logger.warning("C411: Session expired or missing, logging in...")
                    if await get_c411_cookies():
                        with open(cookie_path, 'r') as f:
                            cookies = json.load(f)
                            await context.add_cookies(cookies)
                        response = await context.request.get("https://c411.org/api/auth/me")
                        api_data = await response.json() if response.ok else {}

                user_data = api_data.get("user")
                if user_data:
                    up = user_data.get("uploaded", 0)
                    dl = user_data.get("downloaded", 0)
                    res["upload"] = format_bytes(up)
                    res["download"] = format_bytes(dl)
                    ratio = user_data.get("ratio")
                    if ratio is not None:
                        res["ratio"] = f"{ratio:.2f}" if isinstance(ratio, (int, float)) else str(ratio)
                    else:
                        res["ratio"] = f"{up / dl:.2f}" if dl > 0 else "∞" if up > 0 else "0.00"
                else:
                    return {"ratio": "Auth Error", "upload": "N/A", "download": "N/A"}

            return res
        except Exception as e:
            logger.error(f"Error {site}: {e}")
            return {"ratio": "Error", "upload": "N/A", "download": "N/A"}
        finally:
            await browser.close()
    return {"ratio": "Error", "upload": "N/A", "download": "N/A"}
