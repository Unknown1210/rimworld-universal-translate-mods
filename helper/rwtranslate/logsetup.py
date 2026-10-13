"""Detailed logging + crash reports for the helper.

Files (in <data>/logs):
  helper.log        rotating (1 MB x 5), every request/model/engine event, full tracebacks
  crash-<time>.txt  written for any uncaught exception (main or thread): traceback, environment,
                    installed models, area counters and the last 200 log lines
"""
import collections
import datetime
import logging
import logging.handlers
import platform
import sys
import threading
import traceback

from . import __version__
from .paths import data_dir, logs_dir

_RING = collections.deque(maxlen=200)
_FAILURES = collections.Counter()
_installed = False


class _RingHandler(logging.Handler):
    def emit(self, record):
        try:
            _RING.append(self.format(record))
        except Exception:
            pass


class _CountHandler(logging.Handler):
    """Counts ERROR+ per area (logger name) for the crash report."""
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            _FAILURES[record.name] += 1


def setup(debug=False, console=True):
    global _installed
    root = logging.getLogger("rwt")
    if _installed:
        root.setLevel(logging.DEBUG if debug else logging.INFO)
        return root
    _installed = True
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    fmt = logging.Formatter("%(asctime)s.%(msecs)03d [%(levelname)s] [T%(thread)d] [%(name)s] %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    try:
        fh = logging.handlers.RotatingFileHandler(logs_dir() / "helper.log", maxBytes=1_000_000,
                                                  backupCount=5, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError as e:  # logging must never stop the helper
        sys.stderr.write(f"[rwtranslate] cannot open log file: {e}\n")
    if sys.stderr is not None:                  # the windowed .exe has no console at all
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        sh.setLevel(logging.INFO if console else logging.WARNING)   # quiet for short commands; full detail always goes to the file
        root.addHandler(sh)
    rh = _RingHandler()
    rh.setFormatter(fmt)
    root.addHandler(rh)
    root.addHandler(_CountHandler())
    sys.excepthook = _excepthook
    threading.excepthook = _thread_excepthook
    log_session_header(root, to_console=console)
    return root


def get(area):
    return logging.getLogger("rwt." + area)


def environment():
    info = {
        "helper_version": __version__,
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "frozen": bool(getattr(sys, "frozen", False)),
        "data_dir": str(data_dir()),
    }
    for mod in ("ctranslate2", "sentencepiece"):
        try:
            info[mod] = __import__(mod).__version__
        except Exception as e:
            info[mod] = f"UNAVAILABLE ({type(e).__name__}: {e})"
    try:
        from . import models
        info["installed_models"] = models.installed_pairs()
    except Exception as e:
        info["installed_models"] = f"ERROR {type(e).__name__}: {e}"
    return info


def log_session_header(logger, to_console=True):
    logger.info("=== rwtranslate session start ===")
    for k, v in environment().items():
        logger.info("env %s = %s", k, v)


def write_crash_report(kind, exc_type, exc, tb, extra=None):
    """Write crash-<time>.txt and return its path (None if even that fails)."""
    try:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = logs_dir() / f"crash-{stamp}.txt"
        lines = [f"RWTRANSLATE CRASH REPORT ({kind})", f"time: {datetime.datetime.now().isoformat()}",
                 f"thread: {threading.current_thread().name}", "", "--- exception ---",
                 "".join(traceback.format_exception(exc_type, exc, tb)), "--- environment ---"]
        lines += [f"{k}: {v}" for k, v in environment().items()]
        lines += ["", "--- errors per area (this session) ---"]
        lines += [f"{k}: {v}" for k, v in _FAILURES.most_common()] or ["(none)"]
        if extra:
            lines += ["", "--- context ---"] + [f"{k}: {v}" for k, v in extra.items()]
        lines += ["", "--- last log lines ---"] + list(_RING)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
    except Exception as e:
        sys.stderr.write(f"[rwtranslate] could not write crash report: {e}\n")
        return None


def _excepthook(exc_type, exc, tb):
    if issubclass(exc_type, KeyboardInterrupt):
        return sys.__excepthook__(exc_type, exc, tb)
    log = get("crash")
    log.critical("UNCAUGHT EXCEPTION in main thread", exc_info=(exc_type, exc, tb))
    p = write_crash_report("main-thread", exc_type, exc, tb)
    sys.stderr.write(f"[rwtranslate] fatal error. Crash report: {p}\n")


def _thread_excepthook(args):
    log = get("crash")
    log.critical("UNCAUGHT EXCEPTION in thread %s", getattr(args.thread, "name", "?"),
                 exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    write_crash_report("thread", args.exc_type, args.exc_value, args.exc_traceback,
                       {"thread": getattr(args.thread, "name", "?")})
