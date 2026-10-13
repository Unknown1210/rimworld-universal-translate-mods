#!/usr/bin/env python3
"""Every AT_* key the C# code can ask for must exist in the English and Portuguese files (no red "missing key" text in game)."""
import pathlib, re, sys
root = pathlib.Path(__file__).resolve().parent.parent
xml = {l: set(re.findall(r"<(AT_\w+)>", (root / "Languages" / l / "Keyed" / "AutoTranslate.xml").read_text(encoding="utf-8")))
       for l in ("English", "PortugueseBrazilian", "Portuguese")}
src = "\n".join(p.read_text(encoding="utf-8") for p in (root / "Source").rglob("*.cs"))
used = {k for k in re.findall(r'"(AT_\w+)"', src) if not k.endswith("_")}   # "AT_St_" / "AT_Mode_" are prefixes built at run time
used.add("AT_St_notstarted")    # the initial status key
used |= {"AT_St_" + k for k in re.findall(r'SetStatus\("(\w+)"', src)}
used |= {"AT_Mode_" + m for m in ("auto", "native", "third", "mine")}
bad = 0
for lang, keys in xml.items():
    for k in sorted(used - keys):
        print(f"MISSING in {lang}: {k}"); bad += 1
for other in ("PortugueseBrazilian", "Portuguese"):
    if xml["English"] != xml[other]:
        print(f"English/{other} key sets differ:", sorted(xml["English"] ^ xml[other])); bad += 1
unused = xml["English"] - used
print(f"{len(used)} keys used, {len(xml['English'])} defined" + (f", unused: {sorted(unused)}" if unused else ""))
sys.exit(1 if bad else 0)
