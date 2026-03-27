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


def load_file(filename, is_json: bool = False):
    config_dir = os.getenv("CONFIG_DIR", ".config")
    path = Path(config_dir)
    if not path.is_absolute():
        path = Path(__file__).parent / path
    if not path.exists():
        raise FileNotFoundError(f"File not found : {path}")
    with open(path / filename, "r") as f:
        if is_json:
            return json.load(f)
        else:
            return f.read()


def write_file(filename, content):
    config_dir = os.getenv("CONFIG_DIR", ".config")
    dir_path = Path(config_dir)
    if not dir_path.is_absolute():
        dir_path = Path(__file__).parent / dir_path
    if not dir_path.exists():
      dir_path.mkdir(parents=True, mode=0o700, exist_ok=True)
      
    file_path = dir_path / filename
    with open(file_path, "w") as f:
        f.write(content)
    file_path.chmod(0o600)


class UnknownTrackerError(Exception):
    pass


class ScrappingError(Exception):
    pass
