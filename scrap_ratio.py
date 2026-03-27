import argparse
import asyncio
import os
import sys
import json
import logging
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scrap_ratio")

from scraper import get_stats

async def main():
    parser = argparse.ArgumentParser(description="Get stats from Torr9.net or C411.org via API")
    parser.add_argument("--site", choices=["torr9", "c411", "both"], required=True, help="Site to get stats from")
    parser.add_argument("--no-headless", action="store_false", dest="headless", default=True, help="Run browser in non-headless mode")
    
    args = parser.parse_args()
    
    sites = ["torr9", "c411"] if args.site == "both" else [args.site]
    
    for s in sites:
        print(f"--- {s.upper()} ---")
        stats = await get_stats(s, args.headless)
        if isinstance(stats, dict):
            print(f"Ratio: {stats['ratio']}")
            print(f"Upload: {stats['upload']}")
            print(f"Download: {stats['download']}")
        else:
            print(stats)

if __name__ == "__main__":
    asyncio.run(main())
