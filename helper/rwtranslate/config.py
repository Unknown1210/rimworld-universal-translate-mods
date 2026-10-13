"""Small shared settings file: <data>/config.json. The helper writes it, the game mod reads it.
Keys: target (language code chosen in the helper window), ui_lang, mod_dir, mods_dirs."""
import json
import os

from .paths import data_dir


def _file():
    return data_dir() / "config.json"


def load():
    try:
        d = json.loads(_file().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def get(key, default=None):
    return load().get(key, default)


def set(key, value):  # noqa: A001 - mirrors dict API
    """Merge-safe, atomic write."""
    d = load()
    if value is None:
        d.pop(key, None)
    else:
        d[key] = value
    f = _file()
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)
