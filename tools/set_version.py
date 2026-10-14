#!/usr/bin/env python3
"""Sync the project version everywhere from the VERSION file ("0.NNN"), or set it: tools/set_version.py 0.002

Files updated: helper/pyproject.toml, helper/rwtranslate/__init__.py, mod/AutoTranslate.csproj, mod/AutoTranslate17.csproj, README.md (language chooser), README.br.md (Portuguese) and README.en.md (the "current version" mentions).
`--check` only verifies they match (used by CI). Format is 0.NNN (three digits: 0.001, 0.002, ...) while the project is pre-1.0;
the 3-part form 0.NNN.0 is used where the toolchain requires it (pip, .NET).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def three(v):
    return v + ".0" if v.count(".") == 1 else v


def targets(v):
    t = three(v)
    return [
        (ROOT / "helper/pyproject.toml", r'(?m)^version = "[^"]+"', f'version = "{t}"'),
        (ROOT / "helper/rwtranslate/__init__.py", r'__version__ = "[^"]+"', f'__version__ = "{t}"'),
        (ROOT / "README.br.md", r"\*\*Versão atual: [^*]+\*\*", f"**Versão atual: {v}**"),
        (ROOT / "README.br.md", r"\(versão atual [^)]*\)", f"(versão atual {v})"),
        (ROOT / "README.md", r"<b>Versão atual / Current version: [^<]+</b>", f"<b>Versão atual / Current version: {v}</b>"),
        (ROOT / "README.en.md", r"\*\*Current version: [^*]+\*\*", f"**Current version: {v}**"),
        (ROOT / "README.en.md", r"\(current version [^)]*\)", f"(current version {v})"),
        (ROOT / "mod/AutoTranslate.csproj", r"<Version>[^<]+</Version>", f"<Version>{t}</Version>"),
        (ROOT / "mod/AutoTranslate17.csproj", r"<Version>[^<]+</Version>", f"<Version>{t}</Version>"),
    ]


def main(argv):
    check = "--check" in argv
    args = [a for a in argv if not a.startswith("--")]
    vf = ROOT / "VERSION"
    if args:
        vf.write_text(args[0] + "\n")
    v = vf.read_text().strip()
    if not re.fullmatch(r"0\.\d{3}", v) and not re.fullmatch(r"\d+\.\d+(\.\d+)?", v):
        sys.exit(f"bad version in VERSION: {v!r}")
    bad = 0
    for path, pat, new in targets(v):
        text = path.read_text()
        if not re.search(pat, text):
            sys.exit(f"pattern not found in {path}")
        if check:
            if new not in text:
                print(f"MISMATCH {path.relative_to(ROOT)}: expected {new}")
                bad += 1
        else:
            path.write_text(re.sub(pat, lambda _m: new, text))
    cl = (ROOT / "CHANGELOG.md").read_text()
    if f"## v{v} " not in cl and f"## v{v}\n" not in cl:
        print(f"MISSING CHANGELOG entry for v{v}")
        bad += 1
    print(("OK" if not bad else "FAILED") + f" version {v}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
