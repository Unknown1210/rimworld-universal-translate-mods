"""Local HTTP API used by the game mod. Binds to 127.0.0.1 only and requires a token.

Every request is logged (id, path, status, duration). The mod sends X-Request-Id so a failure in
the game log can be matched with the line in helper.log. Errors return {error, request_id, type}.
"""
import json
import re
import secrets
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__, activity, languages, logsetup, models
from .engine import EngineError, get_engine
from .paths import port_file, token_file
from . import glossary
from .protect import clean_output, translate_protected

log = logsetup.get("server")
PROTOCOL = 2
MAX_BODY = 4 * 1024 * 1024
MAX_TEXTS = 500
DEFAULT_PORT = 18765


def load_or_create_token():
    f = token_file()
    if f.exists() and f.read_text().strip():
        return f.read_text().strip()
    t = secrets.token_hex(24)
    f.write_text(t)
    try:
        f.chmod(0o600)
    except OSError:
        log.warning("could not restrict permissions of %s", f)
    return t


LAST_GAME_REQUEST = 0.0          # time.time() of the last translation the GAME asked for: the background run of "all mods" steps aside while it is recent


def seconds_since_game_request():
    return time.time() - LAST_GAME_REQUEST


def translate_texts(source, target, texts):
    if languages.same(source, target):
        return list(texts)
    engine = get_engine(source, target)
    out = []
    for t in texts:
        g = glossary.lookup(source, target, t)
        out.append(clean_output(t, g if g is not None else translate_protected(t, engine.translate_batch), target))
    return out


def _code_ok(c):
    return isinstance(c, str) and re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,4})?", c) is not None


class HttpError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def make_handler(token):
    class Handler(BaseHTTPRequestHandler):
        server_version = "rwtranslate/" + __version__

        def log_message(self, *a):  # replaced by our own request log
            pass

        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return len(body)

        def _check_access(self):
            real_port = self.server.server_address[1]
            allowed = {f"127.0.0.1:{real_port}", f"localhost:{real_port}"}
            if self.headers.get("Host", "") not in allowed or self.headers.get("Origin"):
                log.warning("REJECTED request from %s: Host=%r Origin=%r", self.client_address[0],
                            self.headers.get("Host"), self.headers.get("Origin"))
                raise HttpError(403, "forbidden")
            if not secrets.compare_digest(self.headers.get("X-Token", ""), token):
                log.warning("REJECTED request from %s: bad/missing token", self.client_address[0])
                raise HttpError(401, "bad token")

        def _read_json(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise HttpError(413, "body too large")
            try:
                return json.loads(self.rfile.read(n) or b"{}")
            except ValueError as e:
                raise HttpError(400, f"bad json: {e}")

        def _handle(self, method):
            rid = (self.headers.get("X-Request-Id") or secrets.token_hex(4))[:32]
            t0 = time.perf_counter()
            code, size, note = 500, 0, ""
            try:
                self._check_access()
                path = urlparse(self.path).path
                code, payload, note = self._route(method, path)
                size = self._send(code, payload)
            except HttpError as e:
                code, note = e.code, str(e)
                size = self._send(code, {"error": str(e), "request_id": rid})
            except EngineError as e:
                code, note = 409, str(e)
                log.error("[%s] engine unavailable: %s", rid, e)
                size = self._send(code, {"error": str(e), "request_id": rid, "type": "EngineError"})
            except Exception as e:
                code, note = 500, f"{type(e).__name__}: {e}"
                log.error("[%s] UNHANDLED %s %s\n%s", rid, method, self.path, traceback.format_exc())
                try:
                    size = self._send(code, {"error": note, "request_id": rid, "type": type(e).__name__})
                except Exception:
                    log.error("[%s] could not even send the 500 response", rid)
            finally:
                ms = (time.perf_counter() - t0) * 1000
                lvl = log.info if code < 400 else log.warning
                lvl("[%s] %s %s -> %d (%d bytes, %.0f ms) %s", rid, method, self.path, code, size, ms, note)

        def _route(self, method, path):
            if method == "GET" and path == "/health":
                return 200, {"ok": True, "version": __version__, "protocol": PROTOCOL,
                             "installed": models.installed_pairs(),
                             "installing": install_state()}, ""
            if method == "GET" and path == "/suggest":
                q = parse_qs(urlparse(self.path).query)
                game = (q.get("game") or [None])[0]
                return 200, {"suggested": languages.suggest(game), "system": languages.system_language(),
                             "game": languages.code_from_game_language(game) if game else None}, ""
            if method == "GET" and path == "/support":
                q = parse_qs(urlparse(self.path).query)
                src, tgt = (q.get("source") or ["en"])[0], (q.get("target") or [""])[0]
                if not _code_ok(src) or not _code_ok(tgt):
                    raise HttpError(400, "need source and target language codes")
                return 200, models.support(src, tgt), f"support {src}->{tgt}"
            if method == "POST" and path == "/translate":
                data = self._read_json()
                source, target, texts = data.get("source", "en"), data.get("target"), data.get("texts")
                if not _code_ok(source) or not _code_ok(target) or not isinstance(texts, list) or len(texts) > MAX_TEXTS \
                        or not all(isinstance(t, str) for t in texts):
                    raise HttpError(400, "need source/target language codes and texts:list[str] (<=500)")
                global LAST_GAME_REQUEST
                mod = data.get("mod") if isinstance(data.get("mod"), str) else ""
                if mod and not mod.startswith("("):
                    LAST_GAME_REQUEST = time.time()               # a real mod asked (not the "(translator check)" probe)
                t0 = time.perf_counter()
                out = translate_texts(source, target, texts)
                if mod and not mod.startswith("("):
                    LAST_GAME_REQUEST = time.time()
                activity.emit("game", "log_game_batch",
                              {"n": len(texts), "src": source, "tgt": target, "mod": mod[:120] or "?", "chars": sum(map(len, texts)),
                               "ms": int((time.perf_counter() - t0) * 1000),
                               "first": f"{texts[0]}  ->  {out[0]}" if len(texts) <= 3 and texts else ""},
                              pairs=list(zip(texts, out)))
                return 200, {"translations": out}, f"{len(texts)} texts, {sum(map(len, texts))} chars {source}->{target}"
            if method == "POST" and path == "/install":
                data = self._read_json()
                source, target = data.get("source", "en"), data.get("target")
                if not _code_ok(source) or not _code_ok(target):
                    raise HttpError(400, "bad language code")
                activity.emit("model", "log_model_asked", {"src": source, "tgt": target})
                threading.Thread(target=_install_bg, args=(source, target), daemon=True, name=f"install-{source}-{target}").start()
                return 202, {"started": True}, f"install {source}->{target}"
            raise HttpError(404, "not found")

        def do_GET(self):
            self._handle("GET")

        def do_POST(self):
            self._handle("POST")

    return Handler


_install_state = {}  # target -> "running" | "done" | "error: ..."


def install_state():
    return dict(_install_state)


def _install_bg(source, target):
    key = f"{source}>{target}"
    _install_state[key] = "running"
    try:
        models.install(source, target, progress=lambda m: None)
        _install_state[key] = "done"
    except Exception as e:
        _install_state[key] = f"error: {type(e).__name__}: {e}"
        log.error("background install of %s failed: %s", key, e)  # traceback already logged in models


def serve(port=DEFAULT_PORT):
    token = load_or_create_token()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(token))
    port_file().write_text(str(httpd.server_address[1]))
    log.info("listening on 127.0.0.1:%d", httpd.server_address[1])
    return httpd
