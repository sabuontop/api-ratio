import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from dotenv import load_dotenv

from util import MissingCredentialsError, ScrappingError, default_user_agent

load_dotenv()
logger = logging.getLogger()

USER_STATS_URL = "https://tr4ker.net/api/me"


async def get_stats(_: bool = False) -> dict[str, Any]:
    try:
        res: dict[str, Any] = {"raw_upload": 0, "raw_download": 0, "bonus": 0}
        token = os.getenv("TR4KER_TOKEN")
        if not token:
            raise MissingCredentialsError("Missing Tr4ker api token")
        try:
            req = urllib.request.Request(USER_STATS_URL, headers={"User-Agent": default_user_agent, "X-Api-Key": token})
            with urllib.request.urlopen(req) as response:
                api_data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            raise ScrappingError(f"Failed to get Tr4ker stats : HTTP {e.code}, Reason {e.reason}")
        except urllib.error.URLError as e:
            raise ScrappingError(e)

        up = api_data.get("uploaded", 0)
        dl = api_data.get("downloaded", 0)
        bonus_up = api_data.get("bonus_upload", 0)
        bonus_dl = api_data.get("bonus_download", 0)
        res["raw_upload"] = up + bonus_up 
        res["raw_download"] = dl + bonus_dl
        res["bonus"] = float(api_data.get("money", 0))

        return res
    except (MissingCredentialsError, ScrappingError) as e:
            raise e
    except Exception as e:
        raise ScrappingError(e)
