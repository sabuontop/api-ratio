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

from scraper import get_stats

ratios_cache: Dict[str, Any] = {
    "torr9": {"ratio": "N/A", "upload": "N/A", "download": "N/A", "last_updated": None},
    "c411": {"ratio": "N/A", "upload": "N/A", "download": "N/A", "last_updated": None}
}

async def update_all():
    global ratios_cache
    for site in ["torr9", "c411"]:
        stats = await get_stats(site)
        ratios_cache[site] = {**stats, "last_updated": datetime.now().isoformat()}

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(update_all())
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_all, 'interval', hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Scrap Ratio API is running", "endpoints": ["/ratios"]}

@app.get("/ratios")
async def get_ratios(): return ratios_cache

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8679)
