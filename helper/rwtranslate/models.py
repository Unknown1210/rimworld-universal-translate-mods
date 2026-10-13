"""Download/install Argos translation models for any language pair.

A pair model lives in <data>/models/<src>_<tgt>/ . When no direct model exists the helper pivots through English
(src->en and en->tgt, both installed), which is how most non-English pairs are served.
"""
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

from . import activity, languages, logsetup
from .paths import models_dir

log = logsetup.get("models")

INDEX_URL = os.environ.get("RWTRANSLATE_INDEX_URL", "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json")  # env override: tests
PIVOT = "en"


def _open(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "rwtranslate/0.5"}), timeout=60)


_index_mem = {"t": 0.0, "data": None}
INDEX_TTL = 6 * 3600


def load_index(force=False):
    """The Argos model index. Cached in memory (6 h) and on disk, so that support questions still work offline."""
    import time
    from .paths import data_dir
    if not force and _index_mem["data"] is not None and time.time() - _index_mem["t"] < INDEX_TTL:
        return _index_mem["data"]
    cache = data_dir() / "index-cache.json"
    try:
        data = json.load(_open(INDEX_URL))
        try:
            cache.write_text(json.dumps(data))
        except OSError:
            pass
    except Exception:
        log.warning("could not fetch the model index (offline?); trying the cached copy", exc_info=True)
        data = json.loads(cache.read_text())      # raises if there is no copy: callers handle it
    _index_mem.update(t=time.time(), data=data)
    return data


def available_pairs(index=None):
    index = index if index is not None else load_index()
    return sorted({(p["from_code"], p["to_code"]) for p in index})


def available_targets(index=None):
    """Target languages reachable from English, as the codes the program uses (Portuguese is split into pt-BR and pt-PT)."""
    out = set()
    for s, t in available_pairs(index):
        if s != PIVOT:
            continue
        if t == "pb":
            out.add("pt-BR")
        elif t == "pt":
            out.add("pt-PT")
        else:
            out.add(t)
    return sorted(out)


def pair_dir(src, tgt):
    src, tgt = languages.model_code(src), languages.model_code(tgt)
    return models_dir() / f"{src}_{tgt}"


def is_installed(src, tgt):
    return (pair_dir(src, tgt) / "ok").exists()


def installed_pairs():
    out = []
    for p in sorted(models_dir().glob("*_*")):
        if (p / "ok").exists() and "_" in p.name:
            s, t = p.name.split("_", 1)
            out.append(f"{s}>{t}")
    return out


def installed_targets():
    """Back-compat for the CLI: targets reachable from English."""
    return sorted(p.split(">")[1] for p in installed_pairs() if p.startswith(PIVOT + ">"))


def plan(src, tgt, index=None):
    """Steps (list of (src,tgt)) needed to translate src->tgt: direct, or pivot through English."""
    if languages.same(src, tgt):
        return []
    src, tgt = languages.model_code(src), languages.model_code(tgt)
    pairs = set(available_pairs(index))
    if (src, tgt) in pairs:
        return [(src, tgt)]
    if src != PIVOT and tgt != PIVOT and (src, PIVOT) in pairs and (PIVOT, tgt) in pairs:
        return [(src, PIVOT), (PIVOT, tgt)]
    raise RuntimeError(f"no model path for {src}->{tgt} in the Argos index (needs a direct model, or both {src}->en and en->{tgt})")


def installed_plan(src, tgt):
    """Offline: how to translate src->tgt with what is installed now (list of steps) or None."""
    if languages.same(src, tgt):
        return []
    src, tgt = languages.model_code(src), languages.model_code(tgt)
    if is_installed(src, tgt):
        return [(src, tgt)]
    if src != PIVOT and tgt != PIVOT and is_installed(src, PIVOT) and is_installed(PIVOT, tgt):
        return [(src, PIVOT), (PIVOT, tgt)]
    return None


def install(src, tgt, progress=print, index=None):
    """Install what is needed for src->tgt (direct or via English). Idempotent."""
    if installed_plan(src, tgt) is not None:
        return
    index = index if index is not None else load_index()
    for s, t in plan(src, tgt, index):
        _install_pair(s, t, progress, index)


def _install_pair(src, tgt, progress, index):
    if is_installed(src, tgt):
        return
    cands = [p for p in index if p["from_code"] == src and p["to_code"] == tgt]
    if not cands:
        raise RuntimeError(f"no {src}->{tgt} model in the Argos index")
    pkg = max(cands, key=lambda p: [int(x) for x in str(p["package_version"]).split(".") if x.isdigit()])
    url = pkg["links"][0]
    dest = pair_dir(src, tgt)
    tmp = models_dir() / f"{src}_{tgt}.download"
    if dest.exists():
        shutil.rmtree(dest)
    progress(f"Baixando modelo {src}->{tgt} ({url}) ...")
    activity.emit("model", "log_model_download", {"src": src, "tgt": tgt, "url": url})
    log.info("downloading model %s->%s version=%s url=%s", src, tgt, pkg["package_version"], url)
    try:
        _download_and_unpack(url, tmp, dest, progress)
    except Exception:
        log.exception("model install FAILED %s->%s url=%s dest=%s", src, tgt, url, dest)
        activity.emit("model", "log_model_failed", {"src": src, "tgt": tgt}, level="error")
        if tmp.exists():
            tmp.unlink()
        shutil.rmtree(dest, ignore_errors=True)  # never leave a half-installed model
        raise
    (dest / "ok").write_text(str(pkg["package_version"]))
    log.info("model %s->%s installed (%d files)", src, tgt, sum(1 for _ in dest.rglob("*")))
    progress("Modelo instalado.")
    activity.emit("model", "log_model_done", {"src": src, "tgt": tgt})


def _download_and_unpack(url, tmp, dest, progress):
    with _open(url) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                progress(f"  {done * 100 // total}% ({done >> 20} MB)")
    with zipfile.ZipFile(tmp) as z:
        for m in z.namelist():  # zip-slip guard
            if Path(m).is_absolute() or ".." in Path(m).parts:
                raise RuntimeError("unsafe path in model archive")
        z.extractall(dest)
    tmp.unlink()


def support(src, tgt, index=None):
    """Can src->tgt be translated? {"known","supported","installed","steps","download"}.
    known=False means the index could not be read and nothing installed covers the pair (answer unknown)."""
    if languages.same(src, tgt):
        return {"known": True, "supported": True, "installed": True, "steps": [], "download": []}
    steps = installed_plan(src, tgt)
    if steps is not None:
        return {"known": True, "supported": True, "installed": True, "steps": [f"{a}>{b}" for a, b in steps], "download": []}
    try:
        steps = plan(src, tgt, index)
    except RuntimeError:
        return {"known": True, "supported": False, "installed": False, "steps": [], "download": []}
    except Exception:                      # index unreachable and no cached copy
        return {"known": False, "supported": False, "installed": False, "steps": [], "download": []}
    todo = [f"{a}>{b}" for a, b in steps if not is_installed(a, b)]
    return {"known": True, "supported": True, "installed": False, "steps": [f"{a}>{b}" for a, b in steps], "download": todo}
