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


MODELS_FOLDER = "translation models"
OLD_MODELS_FOLDER = "models"


def models_dir() -> Path:
    """<data>/translation models. The folder was called "models" before: it is moved (not downloaded again) the first time."""
    base = data_dir()
    p = base / MODELS_FOLDER
    old = base / OLD_MODELS_FOLDER
    if not p.exists() and old.is_dir():
        try:
            old.rename(p)
        except OSError:
            return old                                   # could not move it (in use?): keep using the old folder
    p.mkdir(parents=True, exist_ok=True)
    return p


CACHE_FOLDER = "translated mods"
OLD_CACHE_FOLDER = "cache"


def cache_dir() -> Path:
    """<data>/translated mods: the saved translations, one folder per language, one file per mod (the game mod reads the same folder).
    It was called "cache" before: the old folder is moved (or, if both exist, its files are moved in without overwriting anything)."""
    base = data_dir()
    p = base / CACHE_FOLDER
    old = base / OLD_CACHE_FOLDER
    if old.is_dir():
        try:
            if not p.exists():
                old.rename(p)
            else:
                for src in list(old.rglob("*")):
                    if src.is_file():
                        dst = p / src.relative_to(old)
                        if not dst.exists():
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            src.replace(dst)
        except OSError:
            pass
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
