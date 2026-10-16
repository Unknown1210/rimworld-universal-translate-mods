"""Export the translations of a mod as RimWorld language files, for the people who make mods.

For every mod and language it writes the same files a translator would write by hand:

    <destination>/<mod folder>/<same sub folder as the Defs>/Languages/<RimWorld language folder>/DefInjected/<DefType>/<file>.xml
    <destination>/<mod folder>/<same sub folder as the Defs>/Languages/<RimWorld language folder>/Keyed/<file>.xml

so the folder "Languages" can be copied into the mod as it is (the game then loads it like any other translation). Only the
texts this program translated are written (a text that already had a translation, or was already in the language, is left out).
The texts come from what the program saved (<translated mods>/<language>/<package id>.json) plus the player's corrections."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from . import bulk, logsetup

log = logsetup.get("export")

# language code used by the program -> name of the language folder RimWorld looks for (Languages/<name>)
GAME_FOLDER = {
    "ca": "Catalan", "zh": "ChineseSimplified", "zh-Hant": "ChineseTraditional", "nl": "Dutch", "en": "English", "et": "Estonian",
    "fi": "Finnish", "fr": "French", "de": "German", "el": "Greek", "it": "Italian", "ja": "Japanese", "ko": "Korean",
    "ko-FC": "KoreanFastChannel", "nb": "Norwegian", "pt-BR": "PortugueseBrazilian", "pt-PT": "Portuguese", "ro": "Romanian",
    "ru": "Russian", "sk": "Slovak", "es": "Spanish", "es-419": "SpanishLatin", "sv": "Swedish", "tr": "Turkish",
    "uk": "Ukrainian", "vi": "Vietnamese", "cs": "Czech", "da": "Danish", "hu": "Hungarian", "pl": "Polish",
}
_NAME = re.compile(r"^[A-Za-z_][\w.\-]*$")
README = """Exported by Universal Translate (automatic translation, may contain mistakes).
Copy the folder "Languages" of each language into your mod (next to "Defs") and review the texts.
Exportado pelo Universal Translate (tradução automática, pode conter erros).
Copie a pasta "Languages" de cada idioma para dentro do seu mod (ao lado de "Defs") e revise os textos.
"""


def game_folder(code):
    """The RimWorld language folder of a language code ("pt-BR" -> "PortugueseBrazilian")."""
    return GAME_FOLDER.get(code) or GAME_FOLDER.get(bulk.languages.norm_target(code)) or code


def _translations(code, mod):
    """{normalized original: translation} for one language: the saved translations with the player's corrections on top."""
    tr = {bulk.normalize(k): v for k, v in bulk.read_cache(code, mod.package_id).items()}
    for k, v in bulk.read_overrides(code).items():
        if bulk.normalize(k) in tr:
            tr[bulk.normalize(k)] = v
    return tr


def _write(path, entries):
    root = ET.Element("LanguageData")
    for name, text in entries:
        ET.SubElement(root, name).text = text.replace("\r\n", "\n").replace("\n", "\\n")
    ET.indent(root, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def export_mod(mod, codes, dest):
    """Write the files of one mod for every language in `codes` under `dest`. Returns {"files": n, "texts": n, "languages": [codes written]}."""
    out_root = Path(dest) / bulk.safe_file_name(mod.path.name or mod.package_id)
    result = {"files": 0, "texts": 0, "languages": []}
    for code in codes:
        trans = _translations(code, mod)
        if not trans:
            continue
        written = 0
        folder = game_folder(code)
        for d in bulk.content_dirs(mod):
            rel = d.relative_to(mod.path)
            lang_dir = out_root / rel / "Languages" / folder
            defs = d / "Defs"
            for f in sorted(defs.rglob("*.xml")) if defs.is_dir() else []:
                root = bulk._parse(f)
                if root is None:
                    continue
                groups = {}                                     # def type -> [(name, text)]
                for el in root:
                    if not isinstance(el.tag, str):
                        continue
                    name = (el.findtext("defName") or "").strip()
                    if not name:
                        continue
                    for field in bulk.DEF_FIELDS:
                        c = el.find(field)
                        if c is None:
                            continue
                        src = bulk.normalize("".join(c.itertext()))
                        tr = trans.get(src) if src else None
                        key = f"{name}.{field}"
                        if tr and tr != src and _NAME.match(key):
                            groups.setdefault(el.tag, []).append((key, tr))
                for tag, entries in groups.items():
                    if _NAME.match(tag):
                        _write(lang_dir / "DefInjected" / tag / f.name, entries)
                        result["files"] += 1
                        written += len(entries)
            langs = d / "Languages"
            for ld in sorted(p for p in langs.iterdir() if p.is_dir()) if langs.is_dir() else []:
                if bulk.languages.code_from_game_language(ld.name) != "en":
                    continue
                for f in sorted((ld / "Keyed").rglob("*.xml")) if (ld / "Keyed").is_dir() else []:
                    root = bulk._parse(f)
                    if root is None:
                        continue
                    entries = []
                    for el in root:
                        if not isinstance(el.tag, str):
                            continue
                        src = bulk.normalize("".join(el.itertext()))
                        tr = trans.get(src) if src else None
                        if tr and tr != src and _NAME.match(el.tag):
                            entries.append((el.tag, tr))
                    if entries:
                        _write(lang_dir / "Keyed" / f.relative_to(ld / "Keyed"), entries)
                        result["files"] += 1
                        written += len(entries)
        if written:
            result["texts"] += written
            result["languages"].append(code)
    if result["files"]:
        (out_root / "README.txt").write_text(README, encoding="utf-8")
    return result


def export_all(mods, codes, dest):
    """Export several mods. Returns {"mods": n with files, "files": n, "texts": n, "languages": [codes], "folder": dest}."""
    total = {"mods": 0, "files": 0, "texts": 0, "languages": [], "folder": str(dest)}
    for m in mods:
        try:
            r = export_mod(m, codes, dest)
        except OSError:
            log.exception("could not export %s", m.package_id)
            raise
        if r["files"]:
            total["mods"] += 1
            total["files"] += r["files"]
            total["texts"] += r["texts"]
            total["languages"] = sorted(set(total["languages"]) | set(r["languages"]))
    return total
