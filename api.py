import asyncio, os, re, logging, json
from datetime import datetime
from typing import Dict, Any, Tuple
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from playwright.async_api import async_playwright
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

ratios_cache: Dict[str, Any] = {
    "torr9": {"ratio": "N/A", "upload": "N/A", "download": "N/A", "last_updated": None},
    "c411": {"ratio": "N/A", "upload": "N/A", "download": "N/A", "last_updated": None}
}

def format_bytes(size: float) -> str:
    if size is None or size < 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} EB"

async def scrape_site(site: str) -> Tuple[str, str, str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        try:
            res = {"r": "N/A", "u": "N/A", "d": "N/A"}
            
            if site == "torr9":
                token = os.getenv("TORR9_TOKEN")
                if not token:
                    return "No Token", "N/A", "N/A"
                
                response = await context.request.get(
                    "https://api.torr9.net/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if not response.ok:
                    return f"API Error {response.status}", "N/A", "N/A"
                
                api_data = await response.json()
                up = api_data.get("total_uploaded_bytes", 0)
                dl = api_data.get("total_downloaded_bytes", 0)
                res["u"] = format_bytes(up)
                res["d"] = format_bytes(dl)
                res["r"] = f"{up / dl:.2f}" if dl > 0 else "∞" if up > 0 else "0.00"

            else:
                cookie_path = "c411_cookies.json"
                if not os.path.exists(cookie_path):
                    return "No Cookies", "N/A", "N/A"
                
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                
                response = await context.request.get("https://c411.org/api/auth/me")
                if not response.ok:
                    return f"API Error {response.status}", "N/A", "N/A"
                    
                api_data = await response.json()
                user_data = api_data.get("user")
                if user_data:
                    up = user_data.get("uploaded", 0)
                    dl = user_data.get("downloaded", 0)
                    res["u"] = format_bytes(up)
                    res["d"] = format_bytes(dl)
                    ratio = user_data.get("ratio")
                    if ratio is not None:
                        res["r"] = f"{ratio:.2f}" if isinstance(ratio, (int, float)) else str(ratio)
                    else:
                        res["r"] = f"{up / dl:.2f}" if dl > 0 else "∞" if up > 0 else "0.00"
                else:
                    return "Auth Error", "N/A", "N/A"

            return res["r"], res["u"], res["d"]
        except Exception as e:
            logger.error(f"Error {site}: {e}")
            return "Error", "N/A", "N/A"
        finally:
            await browser.close()

async def update_all():
    global ratios_cache
    for site in ["torr9", "c411"]:
        r, up, dl = await scrape_site(site)
        ratios_cache[site] = {"ratio": r, "upload": up, "download": dl, "last_updated": datetime.now().isoformat()}

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(update_all())
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_all, 'interval', hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
@app.get("/ratios")
async def get_ratios(): return ratios_cache

if __name__ == "__main__":
    import uvicorn
    os.system("taskkill /f /im python.exe /fi \"windowtitle eq api_server\"")
    uvicorn.run(app, host="0.0.0.0", port=8679)
