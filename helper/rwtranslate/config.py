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


def migrate_portuguese():
    """Settings made before Portuguese was split into Brazil and Portugal said "pt": that meant Brazilian Portuguese.
    Rename the saved translations, the manual corrections and the bulk state to "pt-BR" (nothing is overwritten) and fix the target."""
    from .paths import cache_dir, data_dir
    d = data_dir()
    cache_dir()                                           # (moves the old "cache" folder first, if there is one)
    for sub, old, new in (("translated mods", "pt", "pt-BR"), ("overrides", "pt.json", "pt-BR.json")):
        a, b = d / sub / old, d / sub / new
        try:
            if a.exists() and not b.exists():
                a.rename(b)
        except OSError:
            pass
    try:
        f = d / "bulk-state.json"
        st = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        if isinstance(st, dict) and "pt" in st and "pt-BR" not in st:
            st["pt-BR"] = st.pop("pt")
            f.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    except (OSError, ValueError):
        pass
    if load().get("target") == "pt":
        set("target", "pt-BR")
