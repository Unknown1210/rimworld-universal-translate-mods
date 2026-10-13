"""Activity log shown in the window's "Log" tab: what the program is doing, in detail.

Everything that happens is written here as an entry: translations the game asked for (which mod, every original text and its
translation), the bulk run of the "Translate mods" tab, model downloads, updates, and warnings/errors from the other loggers.
Entries keep a message KEY and its arguments instead of finished text, so the window can show them again in another
language when the player switches it. Entries that carry raw technical text (key None) are shown as they are.
Thread safe: the server, the bulk thread and the updater all call emit(); listeners must hand the entry over to the UI thread.
"""
import collections
import logging
import threading
import time

MAX_ENTRIES = 3000
MAX_DETAIL_PAIRS = 400
KINDS = ("game", "bulk", "model", "update", "system")

_lock = threading.Lock()
_entries = collections.deque(maxlen=MAX_ENTRIES)
_listeners = []


class Entry:
    __slots__ = ("when", "kind", "level", "key", "args", "detail", "pairs")

    def __init__(self, kind, key, args, level, detail, pairs):
        self.when, self.kind, self.level = time.time(), kind, level
        self.key, self.args, self.detail, self.pairs = key, args or {}, detail or "", pairs or []

    def detail_text(self):
        """Plain text of the details: the free text, then 'original -> translation' for each pair."""
        parts = [self.detail] if self.detail else []
        for a, b in self.pairs:
            parts.append(f"{a}\n   -> {b}")
        return "\n".join(parts)


def emit(kind, key, args=None, level="info", detail="", pairs=None):
    """Record one thing that happened. key: i18n key ("log_...") or None with args={"text": raw text}. Never raises."""
    try:
        e = Entry(kind, key, args, level, detail, list(pairs or [])[:MAX_DETAIL_PAIRS])
        with _lock:
            _entries.append(e)
            listeners = list(_listeners)
        for fn in listeners:
            try:
                fn(e)
            except Exception:  # noqa: BLE001 - a broken listener must not break the program
                pass
        return e
    except Exception:  # noqa: BLE001
        return None


def snapshot():
    with _lock:
        return list(_entries)


def clear():
    with _lock:
        _entries.clear()


def subscribe(fn):
    with _lock:
        if fn not in _listeners:
            _listeners.append(fn)


def unsubscribe(fn):
    with _lock:
        if fn in _listeners:
            _listeners.remove(fn)


class LogHandler(logging.Handler):
    """Warnings and errors of every logger of the program also appear in the Log tab (with the traceback in the details)."""

    def emit(self, record):
        try:
            if record.levelno < logging.WARNING:
                return
            detail = ""
            if record.exc_info:
                detail = logging.Formatter().formatException(record.exc_info)
            emit("system", None, {"text": f"[{record.name}] {record.getMessage()}"},
                 level="error" if record.levelno >= logging.ERROR else "warning", detail=detail)
        except Exception:  # noqa: BLE001
            pass


_handler = None


def install_log_handler():
    """Attach LogHandler to the root logger once."""
    global _handler
    if _handler is None:
        _handler = LogHandler()
        logging.getLogger().addHandler(_handler)
