import urllib.request
import urllib.error
import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

from util import default_user_agent, MissingCredentialsError, ScrappingError

load_dotenv()
logger = logging.getLogger()

USER_STATS_URL = "https://nexum-core.com/api/v1/me"


async def get_stats(_: bool = False) -> Dict[str, Any]:
    """
    Scraper for Nexum core tracker (Custom API).
    Uses the apikey query parameter for authentication.
    """
    try:
        res: Dict[str, Any] = {"raw_upload": 0, "raw_download": 0, "bonus": 0.0}

        token = os.getenv("NEXUM_API_KEY")
        if not token:
            raise MissingCredentialsError("Missing Nexum API key (NEXUM_API_KEY). Check your .env file.")

        url = f"{USER_STATS_URL}?apikey={token}"

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": default_user_agent,
                "Accept": "application/json"
            })
            with urllib.request.urlopen(req) as response:
                api_data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            raise ScrappingError(f"Nexum: API Error (HTTP {e.code}: {e.reason})")
        except urllib.error.URLError as e:
            raise ScrappingError(f"Nexum: Connection error ({e.reason})")

        res["raw_upload"] = float(api_data.get("uploaded", 0))
        res["raw_download"] = float(api_data.get("downloaded", 0))
        res["bonus"] = float(api_data.get("bonus_points", 0))

        res["web_url"] = "https://nexum-core.com/activity"
        res["bonus_per_10gb"] = 1500

        return res
    except (MissingCredentialsError, ScrappingError) as e:
            raise e
    except Exception as e:
        logger.error(f"Unexpected error in Nexum scrapper: {e}")
        raise ScrappingError(e)
