"""Self-update from GitHub Releases.

check()           -> is there a newer release?  (never raises)
update_helper()   -> download the new .exe, verify SHA-256, swap it in (Windows: rename the running exe, then replace)
update_mod()      -> download the mod zip, verify SHA-256, extract over the installed mod folder
Safety: HTTPS only, GitHub hosts only, SHA-256 taken from the release notes is mandatory. (That protects against
corrupted downloads, not against a compromised repository - trust in the repository is still required.)
A private repository is invisible to anonymous API calls; set RWTRANSLATE_GITHUB_TOKEN to use one.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__, logsetup
from .paths import data_dir

log = logsetup.get("updater")

REPO = "Unknown1210/rimworld-universal-translate-mods"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
HELPER_ASSET = "UniversalTranslate-Helper.exe"
MOD_ASSET = "UniversalTranslate-Mod.zip"
MOD_PACKAGE_ID = "unknown1210.autotranslate"
ALLOWED_HOST_SUFFIXES = ("github.com", "githubusercontent.com")


class UpdateError(Exception):
    """Message is meant to be shown to the user (Portuguese)."""


# ---------------------------------------------------------------- versions

def parse_version(text):
    nums = [int(n) for n in re.findall(r"\d+", text or "")][:3]
    return tuple(nums + [0] * (3 - len(nums)))


def current_version():
    return parse_version(__version__)


def is_frozen():
    return bool(getattr(sys, "frozen", False))


# ---------------------------------------------------------------- network

def _host_ok(url):
    p = urllib.parse.urlparse(url)
    return p.scheme == "https" and any(p.hostname == s or (p.hostname or "").endswith("." + s) for s in ALLOWED_HOST_SUFFIXES)


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects only to GitHub hosts, and never forward the Authorization header to another host
    (GitHub redirects asset downloads to a signed storage URL that rejects it)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _host_ok(newurl):
            raise UpdateError(f"Redirecionamento recusado por segurança: {newurl}")
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlparse(newurl).hostname != urllib.parse.urlparse(req.full_url).hostname:
            new.remove_header("Authorization")
        return new


_opener = urllib.request.build_opener(_SafeRedirect)


def fetch(url, accept=None, progress=None):
    """GET url -> bytes. Raises UpdateError with a friendly message."""
    if not _host_ok(url):
        raise UpdateError(f"Endereço recusado por segurança (só https do GitHub é permitido): {url}")
    headers = {"User-Agent": f"rwtranslate/{__version__}", "Accept": accept or "application/vnd.github+json"}
    token = os.environ.get("RWTRANSLATE_GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with _opener.open(urllib.request.Request(url, headers=headers), timeout=60) as r:
            total = int(r.headers.get("Content-Length") or 0)
            chunks, done = [], 0
            while True:
                c = r.read(1 << 20)
                if not c:
                    break
                chunks.append(c)
                done += len(c)
                if progress and total:
                    progress(f"Baixando... {done * 100 // total}%")
            return b"".join(chunks)
    except urllib.error.HTTPError as e:
        log.warning("HTTP %s for %s", e.code, url)
        if e.code == 404:
            raise UpdateError("Nenhuma versão encontrada no GitHub. O repositório pode estar privado (use a variável RWTRANSLATE_GITHUB_TOKEN) ou ainda não ter releases.")
        if e.code in (401, 403):
            raise UpdateError("O GitHub recusou o acesso (limite de consultas ou repositório privado). Tente de novo mais tarde.")
        raise UpdateError(f"Erro do GitHub (HTTP {e.code}).")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        log.warning("network error for %s: %s", url, e)
        raise UpdateError("Não foi possível falar com o GitHub. Verifique a internet.")


# ---------------------------------------------------------------- release model

@dataclass
class Release:
    tag: str
    version: tuple
    notes: str
    assets: dict = field(default_factory=dict)   # name -> {"url": browser_download_url, "api": api url}
    hashes: dict = field(default_factory=dict)   # asset name -> sha256


_HASH_RE = re.compile(r"\b([0-9a-fA-F]{64})\s+\S*?(UniversalTranslate-[A-Za-z-]+\.(?:exe|zip))")


def parse_release(data):
    tag = data.get("tag_name") or ""
    notes = data.get("body") or ""
    rel = Release(tag=tag, version=parse_version(tag), notes=notes)
    for a in data.get("assets") or []:
        rel.assets[a.get("name")] = {"url": a.get("browser_download_url"), "api": a.get("url")}
    for h, name in _HASH_RE.findall(notes):
        rel.hashes[name] = h.lower()
    return rel


def latest_release(fetcher=fetch):
    try:
        return parse_release(json.loads(fetcher(API_LATEST)))
    except ValueError:
        raise UpdateError("Resposta inesperada do GitHub.")


@dataclass
class Check:
    available: bool = False
    current: str = __version__
    latest: str = ""
    notes: str = ""
    release: object = None
    error: str = ""


def check(fetcher=fetch):
    """Never raises."""
    try:
        rel = latest_release(fetcher)
    except UpdateError as e:
        return Check(error=str(e))
    except Exception as e:  # noqa: BLE001 - the updater must never crash the program
        log.exception("unexpected error while checking for updates")
        return Check(error=f"Erro inesperado: {type(e).__name__}: {e}")
    avail = rel.version > current_version()
    log.info("update check: current=%s latest=%s available=%s", __version__, rel.tag, avail)
    return Check(available=avail, latest=rel.tag, notes=rel.notes, release=rel)


# ---------------------------------------------------------------- download + verify

def download_verified(rel, name, fetcher=fetch, progress=None):
    asset = rel.assets.get(name)
    if not asset:
        raise UpdateError(f"A versão {rel.tag} não contém o arquivo {name}.")
    expected = rel.hashes.get(name)
    if not expected:
        raise UpdateError(f"A versão {rel.tag} não publica o hash (SHA-256) de {name}; atualização recusada por segurança.")
    # The API asset URL works for private repositories (with a token) and public ones; the public link is the fallback.
    data, last = None, None
    for url in [u for u in (asset.get("api"), asset.get("url")) if u]:
        try:
            data = fetcher(url, accept="application/octet-stream", progress=progress)
            break
        except UpdateError as e:
            last = e
            log.warning("download from %s failed (%s); trying the next address", url, e)
    if data is None:
        raise last or UpdateError(f"Sem endereço para baixar {name}.")
    got = hashlib.sha256(data).hexdigest()
    if got != expected:
        log.error("hash mismatch for %s: expected %s got %s", name, expected, got)
        raise UpdateError(f"O arquivo baixado ({name}) não confere com o hash publicado. Atualização cancelada.")
    return data


# ---------------------------------------------------------------- helper (the exe)

def _swap(current: Path, new_bytes: bytes):
    """Replace `current` by new_bytes. Windows lets a running exe be renamed but not overwritten."""
    new = current.with_name(current.name + ".new")
    old = current.with_name(current.name + ".old")
    new.write_bytes(new_bytes)
    try:
        if old.exists():
            old.unlink()
        os.replace(current, old)
        try:
            os.replace(new, current)
        except Exception:
            os.replace(old, current)       # roll back so the program is never left without its exe
            raise
    finally:
        if new.exists():
            new.unlink()


def update_helper(rel, fetcher=fetch, progress=None, exe_path=None):
    """Returns the path of the updated exe. Only meaningful for the packaged exe (or an explicit exe_path)."""
    target = Path(exe_path) if exe_path else (Path(sys.executable) if is_frozen() else None)
    if target is None:
        raise UpdateError("Você está usando a versão Python: atualize com `pip install --upgrade` a partir do ZIP novo do GitHub.")
    data = download_verified(rel, HELPER_ASSET, fetcher, progress)
    _swap(target, data)
    log.info("helper updated to %s at %s", rel.tag, target)
    return target


def cleanup_old():
    """Delete the previous exe left by an update (it could not be removed while running)."""
    if not is_frozen():
        return
    old = Path(sys.executable).with_name(Path(sys.executable).name + ".old")
    try:
        if old.exists():
            old.unlink()
    except OSError:
        pass


def restart(exe=None, args=None):
    """Start the (new) program and let the caller exit. PyInstaller onefile children must not reuse our temp dir."""
    exe = str(exe or sys.executable)
    env = dict(os.environ)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    env.pop("_MEIPASS2", None)
    cmd = [exe] + list(args or ([] if is_frozen() else sys.argv))
    log.info("restarting: %s", cmd)
    subprocess.Popen(cmd, env=env, close_fds=True)


# ---------------------------------------------------------------- the mod folder

def _steam_libraries():
    roots = []
    if sys.platform == "win32":
        for var in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(var)
            if base:
                roots.append(Path(base) / "Steam")
    else:
        roots += [Path.home() / ".steam/steam", Path.home() / ".local/share/Steam"]
    libs = list(roots)
    for r in roots:
        vdf = r / "steamapps" / "libraryfolders.vdf"
        try:
            for m in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(errors="ignore")):
                libs.append(Path(m.replace("\\\\", "\\")))
        except OSError:
            pass
    return libs


def _is_our_mod(p: Path):
    about = p / "About" / "About.xml"
    try:
        return about.exists() and MOD_PACKAGE_ID in about.read_text(errors="ignore").lower()
    except OSError:
        return False


def find_mod_dir(extra_roots=()):
    """Installed AutoTranslate mod folder (RimWorld/Mods/AutoTranslate) or None. <data>/config.json 'mod_dir' wins."""
    cfg = data_dir() / "config.json"
    try:
        saved = json.loads(cfg.read_text()).get("mod_dir")
        if saved and _is_our_mod(Path(saved)):
            return Path(saved)
    except (OSError, ValueError):
        pass
    for lib in list(extra_roots) + _steam_libraries():
        p = Path(lib) / "steamapps" / "common" / "RimWorld" / "Mods" / "AutoTranslate"
        if _is_our_mod(p):
            return p
    return None


def save_mod_dir(path):
    from . import config
    config.set("mod_dir", str(path))


def update_mod(rel, mod_dir, fetcher=fetch, progress=None):
    """Extract the AutoTranslate/ folder of the release zip over the installed mod. Returns number of files written."""
    import io
    data = download_verified(rel, MOD_ASSET, fetcher, progress)
    mod_dir = Path(mod_dir)
    written = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        for n in names:
            parts = Path(n).parts
            if Path(n).is_absolute() or ".." in parts or not parts or parts[0] != "AutoTranslate":
                raise UpdateError("Arquivo do mod com caminho inseguro; atualização cancelada.")
        for n in names:
            rel_path = Path(*Path(n).parts[1:])
            dest = mod_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(z.read(n))
            except PermissionError:
                raise UpdateError(f"Não consegui gravar {dest}. Feche o RimWorld e tente de novo.")
            written += 1
    log.info("mod updated to %s in %s (%d files)", rel.tag, mod_dir, written)
    return written


def save_mod_zip(rel, fetcher=fetch, progress=None):
    """When the mod folder is unknown: keep the verified zip in <data>/updates for a manual install."""
    data = download_verified(rel, MOD_ASSET, fetcher, progress)
    d = data_dir() / "updates"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"UniversalTranslate-Mod-{rel.tag}.zip"
    p.write_bytes(data)
    return p
