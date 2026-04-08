import os
import json
from pathlib import Path
import importlib

default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def list_scrappers():
    folder = Path(__file__).parent.joinpath("scrappers")
    return [f.stem for f in folder.glob("*.py") if not f.name.startswith("_")]


def load_scrapper(name):
    return importlib.import_module(f"scrappers.{name}")


def format_bytes(size: float) -> str:
    if size is None or size < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} EB"


def parse_bytes(size_str: str) -> float:
    if not size_str:
        return 0.0
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
        "PB": 1024**5,
        "EB": 1024**6,
        "KIB": 1024,
        "MIB": 1024**2,
        "GIB": 1024**3,
        "TIB": 1024**4,
        "PIB": 1024**5,
        "EIB": 1024**6,
    }
    parts = size_str.strip().split()
    value = float(parts[0])
    if len(parts) < 2:
        return value
    unit = parts[1].upper()
    return value * units.get(unit, 1)

def _get_config_dir() -> Path:
    config_dir = os.getenv("CONFIG_DIR", ".config")
    path = Path(config_dir)
    if not path.is_absolute():
        path = Path(__file__).parent / path
    return path

def load_file(filename, is_json: bool = False):
    config_dir = _get_config_dir()
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found : {config_dir}")
    with open(config_dir / filename, "r") as f:
        if is_json:
            return json.load(f)
        else:
            return f.read()


def write_file(filename, content):
    config_dir = _get_config_dir()
    if not config_dir.exists():
      config_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    file_path = config_dir / filename
    with open(file_path, "w") as f:
        f.write(content)
    file_path.chmod(0o600)


class UnknownTrackerError(Exception):
    pass


class ScrappingError(Exception):
    pass

class MissingCredentialsError(Exception):
    pass
