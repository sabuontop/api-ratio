import argparse
import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

def format_bytes(size: float) -> str:
    if size is None or size < 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} EB"

async def get_stats(site, headless=True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        try:
            if site == "torr9":
                token = os.getenv("TORR9_TOKEN")
                if not token:
                    return "Error: TORR9_TOKEN not found in .env"
                
                response = await context.request.get(
                    "https://api.torr9.net/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if not response.ok:
                    return f"Error: API returned status {response.status}"
                
                api_data = await response.json()
                up = api_data.get("total_uploaded_bytes", 0)
                dl = api_data.get("total_downloaded_bytes", 0)
                ratio = f"{up/dl:.2f}" if dl > 0 else "∞" if up > 0 else "0.00"
                return {"ratio": ratio, "upload": format_bytes(up), "download": format_bytes(dl)}
                
            elif site == "c411":
                cookie_path = "c411_cookies.json"
                if not os.path.exists(cookie_path):
                    return f"Error: {cookie_path} not found"
                
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                
                response = await context.request.get("https://c411.org/api/auth/me")
                if not response.ok:
                    return f"Error: API returned status {response.status}"
                
                api_data = await response.json()
                user_data = api_data.get("user")
                if user_data:
                    up = user_data.get("uploaded", 0)
                    dl = user_data.get("downloaded", 0)
                    ratio = user_data.get("ratio")
                    if ratio is None:
                        ratio_str = f"{up/dl:.2f}" if dl > 0 else "∞" if up > 0 else "0.00"
                    else:
                        ratio_str = f"{ratio:.2f}" if isinstance(ratio, (int, float)) else str(ratio)
                    
                    return {"ratio": ratio_str, "upload": format_bytes(up), "download": format_bytes(dl)}
                else:
                    return "Error: Authentication failed (check your cookies)"

        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            await browser.close()

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
