"""Window texts in the RimWorld languages other than Portuguese and English.

The English texts are translated with the program's own offline models on first use and cached in <data>/ui/<language>.json,
one entry per text together with a hash of the English text it came from (a changed English text is translated again).
Until a text is ready the window shows it in English; nothing here ever blocks or breaks the window."""
import hashlib
import html
import json
import re
import threading

from . import languages, logsetup
from .paths import data_dir

log = logsetup.get("uitext")
_lock = threading.Lock()
_memo = {}                       # language -> {key: translation} (only entries whose English source is unchanged)
_PLACEHOLDER = re.compile(r"\{[^{}]*\}")


def _en():
    from .i18n import TEXT
    return TEXT["en"]


def _h(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _file(lang):
    return data_dir() / "ui" / f"{lang}.json"


def _read(lang):
    try:
        raw = json.loads(_file(lang).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _clean(text):
    """A machine translation sometimes comes back with HTML entities ("&#160;" for a non-breaking space): show the real character."""
    return html.unescape(text) if "&" in text else text


def load(lang):
    """{key: translation} for the entries that still match the current English text."""
    with _lock:
        if lang not in _memo:
            en = _en()
            ok = {}
            for k, v in _read(lang).items():
                if k in en and isinstance(v, list) and len(v) == 2 and v[0] == _h(en[k]) and isinstance(v[1], str) and v[1]:
                    ok[k] = _clean(v[1])
            _memo[lang] = ok
        return _memo[lang]


def lookup(lang, key):
    return load(lang).get(key)


def pending(lang):
    """Keys that still need a translation."""
    done = load(lang)
    return [k for k in _en() if k not in done]


def model_ready(lang):
    from . import models
    return models.installed_plan("en", lang) is not None


def _same_placeholders(a, b):
    return sorted(_PLACEHOLDER.findall(a)) == sorted(_PLACEHOLDER.findall(b))


def translate_missing(lang, progress=None):
    """Translate every missing text (needs the en->lang model). Returns how many were translated. Saves as it goes."""
    from .engine import get_engine
    from .protect import clean_output, translate_protected
    en = _en()
    todo = pending(lang)
    if not todo:
        return 0
    engine = get_engine("en", lang)
    stored = _read(lang)
    n = 0
    for i, k in enumerate(todo):
        try:
            t = _clean(clean_output(en[k], translate_protected(en[k], engine.translate_batch), lang))
        except Exception:  # noqa: BLE001
            log.exception("could not translate window text %s into %s", k, lang)
            continue
        if not t or not _same_placeholders(en[k], t):
            log.warning("window text %s into %s dropped (empty or lost a placeholder)", k, lang)
            continue
        stored[k] = [_h(en[k]), t]
        with _lock:
            _memo.setdefault(lang, {})[k] = t
        n += 1
        if progress and (i % 20 == 0 or i == len(todo) - 1):
            progress(i + 1, len(todo))
        if n % 25 == 0:
            _save(lang, stored)
    _save(lang, stored)
    return n


def _save(lang, stored):
    f = _file(lang)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(stored, ensure_ascii=False), encoding="utf-8")
    tmp.replace(f)


def forget(lang=None):
    with _lock:
        if lang is None:
            _memo.clear()
        else:
            _memo.pop(lang, None)
