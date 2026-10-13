"""Where the helper keeps models, the auth token and its config."""
import os
import sys
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("RWTRANSLATE_HOME")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "RimWorldAutoTranslate"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "RimWorldAutoTranslate"
    base.mkdir(parents=True, exist_ok=True)
    return base


def models_dir() -> Path:
    p = data_dir() / "models"
    p.mkdir(parents=True, exist_ok=True)
    return p


def token_file() -> Path:
    return data_dir() / "token"


def port_file() -> Path:
    return data_dir() / "port"


def logs_dir() -> Path:
    """Shared by the helper (helper.log, crash-*.txt) and the game mod (mod/ subfolder)."""
    p = data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p
