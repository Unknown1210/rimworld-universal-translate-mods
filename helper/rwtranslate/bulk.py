"""Translate EVERY installed mod, whether or not it is enabled in the game.

It reads the mod folders directly (Steam "Mods" and Workshop folders, plus any folder the user adds), collects the same
texts the game mod collects (Def labels/descriptions, English Keyed texts, the mod description), skips what already has a
translation (the mod's own or another mod's), detects the language of the rest, translates it and writes the SAME
per-mod cache files the game mod reads (<data>/cache/<lang>/<packageId>.json). When the game later runs, those
texts are applied straight from the cache. It is best effort: anything it could not read in advance is simply
translated by the game mod as usual.

Progress is reported through a callback; a state file remembers each mod's fingerprint so that new or changed mods can be
found again later ("search for new mods").
"""
import datetime
import hashlib
import json
import os
import re
import threading
import xml.etree.ElementTree as ET
from pathlib import Path

from . import config, langdetect, languages, logsetup, models, server, updater
from .paths import data_dir

log = logsetup.get("bulk")

DEF_FIELDS = ("label", "description", "labelShort", "labelPlural", "labelNoun", "jobString", "reportString",
              "gerundLabel", "pawnLabel", "adjective", "labelMale", "labelFemale")
MAX_XML = 8 * 1024 * 1024
RIMWORLD_APP_ID = "294100"
BATCH_MAX, BATCH_CHARS = 40, 6000
SKIP_LIST_MAX = 300


# ---------------------------------------------------------------- text helpers (must match the mod's TranslationCache.Norm)

def normalize(s):
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\\n", "\n")
    s = re.sub(r"[ \t]*\n[ \t]*", "\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


def count_words(text):
    """Words; every CJK character counts as one (those languages have no spaces)."""
    return len(re.findall(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]|\w+", text))     # CJK first, or \w+ would swallow the whole run


def safe_file_name(name):
    out = "".join("_" if (c in '<>:"/\\|?*' or ord(c) < 32) else c for c in name)
    return out or "_"


def cache_path(target, package_id):
    return data_dir() / "cache" / target / (safe_file_name(package_id) + ".json")


def read_cache(target, package_id):
    p = cache_path(target, package_id)
    try:
        entries = json.loads(p.read_text(encoding="utf-8")).get("entries", {})
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in entries.items() if isinstance(v, str) and "▁" not in v}


def write_cache(target, package_id, entries):
    p = cache_path(target, package_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps({"format": 1, "target": target, "entries": entries}, ensure_ascii=False, indent=0), encoding="utf-8")
    os.replace(tmp, p)


def clear_translations(target):
    """Delete every saved translation for `target` (the cache files the game reads) and forget what was done, so the mods
    show as new again. The player's manual corrections (overrides) are kept. Returns the number of files deleted."""
    n = 0
    d = data_dir() / "cache" / target
    if d.is_dir():
        for f in d.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                    n += 1
                except OSError:
                    log.warning("could not delete %s", f, exc_info=True)
    st = state_load()
    if st.pop(target, None) is not None:
        state_save(st)
    log.info("cleared %d translation file(s) for %s", n, target)
    return n


# ---------------------------------------------------------------- discovering mods

class ModInfo:
    def __init__(self, path, package_id, name, description):
        self.path, self.package_id, self.name, self.description = Path(path), package_id, name, description
        self.fingerprint = None


def dir_entries(extra=()):
    """Every folder searched for mods, in the order they are searched: [(Path, kind, exists)].
    kind is "default" (Steam's RimWorld/Mods and Workshop folders) or "added" (chosen by the user, saved in config.json).
    Folders the user added are kept even when they do not exist (yet), so the window can say so."""
    cand = []
    for lib in updater._steam_libraries():
        cand += [(lib / "steamapps" / "common" / "RimWorld" / "Mods", "default"),
                 (lib / "steamapps" / "workshop" / "content" / RIMWORLD_APP_ID, "default")]
    cand += [(Path(p), "added") for p in list(extra) + list(config.get("mods_dirs") or [])]
    seen, out = set(), []
    for d, kind in cand:
        exists = d.is_dir()
        if kind == "default" and not exists:
            continue                                      # a default location that is not there is not worth listing
        try:
            key = str(d.resolve())
        except OSError:
            key = str(d)
        if key not in seen:
            seen.add(key)
            out.append((d, kind, exists))
    return out


def mods_dirs(extra=()):
    """Folders that contain mod folders and exist (see dir_entries)."""
    return [d for d, _kind, exists in dir_entries(extra) if exists]


def _parse(path):
    try:
        if path.stat().st_size > MAX_XML:
            log.warning("skipping huge xml file %s", path)
            return None
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError, UnicodeDecodeError) as e:
        log.warning("cannot read %s: %s", path, e)
        return None


def scan(dirs):
    mods, seen = [], set()
    for d in dirs:
        try:
            children = sorted(p for p in Path(d).iterdir() if p.is_dir())
        except OSError:
            continue
        for c in children:
            about = c / "About" / "About.xml"
            if not about.is_file():
                continue
            root = _parse(about)
            if root is None:
                continue
            pid = (root.findtext("packageId") or "").strip()
            if not pid or pid.lower() in seen:
                continue
            seen.add(pid.lower())
            desc = root.findtext("description") or ""
            mods.append(ModInfo(c, pid, (root.findtext("name") or pid).strip(), desc))
    return mods


def content_dirs(mod):
    """Folders of the mod that hold content for game version 1.6: the root, Common, 1.6 / v1.6 and LoadFolders.xml entries."""
    cand = [mod.path, mod.path / "Common", mod.path / "1.6", mod.path / "v1.6"]
    lf = mod.path / "LoadFolders.xml"
    if lf.is_file():
        root = _parse(lf)
        if root is not None:
            for tag in ("v1.6", "default"):
                node = root.find(tag)
                if node is not None:
                    for li in node.findall("li"):
                        rel = (li.text or "").strip().strip("/\\")
                        cand.append(mod.path / rel if rel else mod.path)
                    break
    seen, out = set(), []
    for d in cand:
        k = str(d)
        if d.is_dir() and k not in seen:
            seen.add(k)
            out.append(d)
    return out


def fingerprint(mod):
    h = hashlib.sha1()
    try:
        h.update((mod.path / "About" / "About.xml").read_bytes())
    except OSError:
        pass
    n = 0
    for d in content_dirs(mod):
        for sub in ("Defs", "Languages"):
            for f in sorted((d / sub).rglob("*.xml")) if (d / sub).is_dir() else []:
                try:
                    st = f.stat()
                except OSError:
                    continue
                h.update(f"{f.relative_to(mod.path)}|{st.st_size}|{st.st_mtime_ns}".encode())
                n += 1
                if n > 20000:
                    return h.hexdigest()
    return h.hexdigest()


# ---------------------------------------------------------------- what to translate

def harvest(mod):
    """[(origin, normalized text, cover_key)] for one mod. cover_key lets coverage skip already translated texts."""
    out = []
    for d in content_dirs(mod):
        defs = d / "Defs"
        for f in sorted(defs.rglob("*.xml")) if defs.is_dir() else []:
            root = _parse(f)
            if root is None:
                continue
            for el in root:
                if not isinstance(el.tag, str):
                    continue
                name = (el.findtext("defName") or "").strip()
                for field in DEF_FIELDS:
                    c = el.find(field)
                    if c is None:
                        continue
                    text = normalize("".join(c.itertext()))
                    if text:
                        out.append((f"{el.tag}:{name or '?'}.{field}", text, ("def", el.tag, name, field) if name else None))
        langs = d / "Languages"
        if langs.is_dir():
            for ld in sorted(p for p in langs.iterdir() if p.is_dir()):
                if languages.code_from_game_language(ld.name) != "en":
                    continue
                for f in sorted((ld / "Keyed").rglob("*.xml")) if (ld / "Keyed").is_dir() else []:
                    root = _parse(f)
                    if root is None:
                        continue
                    for el in root:
                        if isinstance(el.tag, str):
                            text = normalize("".join(el.itertext()))
                            if text:
                                out.append((f"Keyed:{el.tag}", text, ("key", el.tag)))
    desc = normalize(mod.description)
    if desc:
        out.append(("ModMeta:description", desc, None))
    return out


def is_placeholder(cover_value, source_text, target):
    """A 'translation' file entry that is not a translation: same text as the original (the game's translation-writing
    tool copies the English text into the files), or text that is confidently in some other language than the target."""
    v = normalize(cover_value)
    if v == normalize(source_text):
        return True
    sl = langdetect.script_lang(v)
    if sl is not None:
        return not languages.same(sl, target)
    lat, conf, _ = langdetect.latin_lang([v])
    return bool(conf and not languages.same(lat, target))


def build_coverage(mods, target):
    """What the installed mods say they translate into `target`: {def field: [(provider mod, value)]} and {Keyed key: [...]}.
    Whether an entry is a REAL translation is decided per text (see is_placeholder)."""
    defs, keys = {}, {}
    target = languages.norm_target(target)               # an old "pt" setting means Brazilian Portuguese (folder PortugueseBrazilian)
    for m in mods:
        for d in content_dirs(m):
            langs = d / "Languages"
            if not langs.is_dir():
                continue
            for ld in (p for p in langs.iterdir() if p.is_dir()):
                if languages.code_from_game_language(ld.name) != target:
                    continue
                di = ld / "DefInjected"
                for f in sorted(di.rglob("*.xml")) if di.is_dir() else []:
                    tag = f.relative_to(di).parts[0] if len(f.relative_to(di).parts) > 1 else None
                    root = _parse(f)
                    for el in (root if root is not None else []):
                        if isinstance(el.tag, str) and "." in el.tag and tag and (el.text or "").strip() not in ("", "TODO"):
                            dn, field = el.tag.split(".", 1)
                            defs.setdefault((tag, dn, field), []).append((m.name, el.text))
                kd = ld / "Keyed"
                for f in sorted(kd.rglob("*.xml")) if kd.is_dir() else []:
                    root = _parse(f)
                    for el in (root if root is not None else []):
                        if isinstance(el.tag, str) and (el.text or "").strip() not in ("", "TODO"):
                            keys.setdefault(el.tag, []).append((m.name, el.text))
    return defs, keys


# ---------------------------------------------------------------- results and state

class ModResult:
    def __init__(self, mod):
        self.package_id, self.name = mod.package_id, mod.name
        self.texts = self.words = self.translated = self.from_cache = self.failed = 0
        self.covered = self.already_target = self.placeholders = 0
        self.skipped = []          # [{"text","reason","detail"}] (capped): why a text was NOT translated by us
        self.langs = {}            # source language -> texts
        self.unsupported = []      # ["ja->pt"]
        self.error = None

    def to_state(self, fp):
        return {"fingerprint": fp, "name": self.name, "texts": self.texts, "words": self.words, "translated": self.translated,
                "from_cache": self.from_cache, "failed": self.failed, "langs": self.langs, "unsupported": self.unsupported,
                "covered": self.covered, "already_target": self.already_target, "placeholders": self.placeholders,
                "skipped": self.skipped[:SKIP_LIST_MAX],
                "when": datetime.datetime.now().isoformat(timespec="seconds")}


def _state_file():
    return data_dir() / "bulk-state.json"


def state_load():
    try:
        return json.loads(_state_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def state_save(st):
    f = _state_file()
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)


def plan(target, dirs=None):
    """[(ModInfo, status, saved_result_or_None)] with status new | changed | ok, comparing fingerprints to what was done before."""
    mods = scan(dirs if dirs is not None else mods_dirs())
    st = state_load().get(target, {})
    out = []
    for m in mods:
        m.fingerprint = fingerprint(m)
        saved = st.get(m.package_id)
        status = "new" if saved is None else ("ok" if saved.get("fingerprint") == m.fingerprint else "changed")
        out.append((m, status, saved))
    return out


# ---------------------------------------------------------------- translating

def _translate_group(src, target, texts, result, cancel, on_batch):
    """Translate texts of one source language; returns {text: translation}. Never raises."""
    out = {}
    i = 0
    while i < len(texts) and not (cancel and cancel.is_set()):
        batch, chars = [], 0
        while i < len(texts) and len(batch) < BATCH_MAX and chars < BATCH_CHARS:
            batch.append(texts[i])
            chars += len(texts[i])
            i += 1
        try:
            for t, tr in zip(batch, server.translate_texts(src, target, batch)):
                out[t] = tr
        except Exception:  # noqa: BLE001 - isolate the failing text, keep going
            log.warning("batch of %d failed (%s->%s); retrying one by one", len(batch), src, target, exc_info=True)
            for t in batch:
                try:
                    out[t] = server.translate_texts(src, target, [t])[0]
                except Exception:  # noqa: BLE001
                    result.failed += 1
                    if len(result.skipped) < SKIP_LIST_MAX:
                        result.skipped.append({"text": t, "reason": "failed", "detail": ""})
                    log.error("could not translate a text of %s: %r", result.package_id, t[:120], exc_info=True)
        on_batch(len(out))
    return out


def process_mod(mod, target, coverage, cancel=None, progress=None, model_ok=None, ensure_model=None):
    """Harvest, filter, translate and cache one mod. Returns a ModResult."""
    res = ModResult(mod)
    progress = progress or (lambda e: None)
    def_cov, key_cov = coverage
    cache = read_cache(target, mod.package_id)
    items = {}
    for origin, text, cov in harvest(mod):
        found = []
        if cov:
            found = def_cov.get(cov[1:], []) if cov[0] == "def" else key_cov.get(cov[1], [])
        real = [(prov, v) for prov, v in found if not is_placeholder(v, text, target)]
        if real:                                              # a REAL translation exists (the mod's own or another mod's): leave it
            res.covered += 1
            if len(res.skipped) < SKIP_LIST_MAX:
                res.skipped.append({"text": text, "reason": "covered", "detail": real[-1][0]})
            continue
        if found and text not in items:
            res.placeholders += 1                             # a translation file exists but only holds the original text: we translate it
        items.setdefault(text, origin)
    if not items:
        return res
    lat, conf, detail = langdetect.latin_lang(list(items))
    log.info("mod %s: Latin-script texts look %s (%s%s)", mod.package_id, lat, "confident; " if conf else "weak, assuming English; ", detail)
    groups = {}
    for text in items:
        lang = langdetect.script_lang(text) or lat
        if languages.same(lang, target):
            res.already_target += 1
            if len(res.skipped) < SKIP_LIST_MAX:
                res.skipped.append({"text": text, "reason": "already_target", "detail": lang})
            continue
        groups.setdefault(lang, []).append(text)
    new_entries = {}
    for lang, texts in groups.items():
        res.langs[lang] = len(texts)
        res.texts += len(texts)
        todo = []
        for t in texts:
            if t in cache:
                res.from_cache += 1
                res.words += count_words(t)
            else:
                todo.append(t)
        if not todo:
            continue
        if ensure_model is not None and not ensure_model(lang):
            res.unsupported.append(f"{lang}->{target}")
            for t in todo:
                if len(res.skipped) < SKIP_LIST_MAX:
                    res.skipped.append({"text": t, "reason": "unsupported", "detail": f"{lang}->{target}"})
            continue
        done0 = res.from_cache + res.translated
        got = _translate_group(lang, target, todo, res, cancel,
                               lambda n: progress({"event": "mod_progress", "name": mod.name, "done": done0 + n, "total": res.texts}))
        for t, tr in got.items():
            new_entries[t] = tr
            res.translated += 1
            res.words += count_words(t)
    if new_entries:
        cache.update(new_entries)
        write_cache(target, mod.package_id, cache)
    return res


def run(target, dirs=None, force=False, progress=None, cancel=None, only_pending=True):
    """Translate pending (new/changed) mods, or all with force=True. Returns the list of ModResult."""
    progress = progress or (lambda e: None)
    items = plan(target, dirs)
    mods = [m for m, _s, _r in items]
    todo = [(m, s) for m, s, _r in items if force or s != "ok"]
    coverage = build_coverage(mods, target)
    ensured = {}

    def ensure_model(src):
        if src in ensured:
            return ensured[src]
        info = models.support(src, target)
        ok = bool(info["supported"])
        if ok and not info["installed"]:
            progress({"event": "model", "pair": f"{src}->{target}"})
            try:
                models.install(src, target, progress=lambda m: None)
            except Exception:  # noqa: BLE001
                log.error("model %s->%s could not be installed", src, target, exc_info=True)
                ok = False
        elif not info["known"] and not info["installed"]:
            ok = False
        ensured[src] = ok
        return ok

    results, total = [], len(todo)
    progress({"event": "start", "total": total, "all": len(mods)})
    st = state_load()
    st.setdefault(target, {})
    for i, (m, status) in enumerate(todo):
        if cancel and cancel.is_set():
            progress({"event": "cancelled", "done": i, "total": total})
            break
        progress({"event": "mod_start", "index": i, "total": total, "name": m.name, "status": status})
        try:
            r = process_mod(m, target, coverage, cancel, progress, ensure_model=ensure_model)
        except Exception as e:  # noqa: BLE001 - one broken mod must not stop the rest
            log.error("mod %s failed during bulk translation", m.package_id, exc_info=True)
            r = ModResult(m)
            r.error = f"{type(e).__name__}: {e}"
        results.append(r)
        if not (cancel and cancel.is_set()) and r.error is None:
            st[target][m.package_id] = r.to_state(m.fingerprint or fingerprint(m))
            state_save(st)
        progress({"event": "mod_done", "index": i + 1, "total": total, "result": r})
    else:
        progress({"event": "finished", "done": total, "total": total})
    return results
