#!/usr/bin/env python3
"""Fails if the mod zip a player downloads lacks something the mod needs at run time
(this is how the screen once showed raw "AT_On" keys: the Languages folder was missing from the zip)."""
import sys
import zipfile

REQUIRED = [
    "AutoTranslate/About/About.xml",
    "AutoTranslate/LoadFolders.xml",
    "AutoTranslate/1.6/Assemblies/RimWorldAutoTranslate.dll",
    "AutoTranslate/Languages/English/Keyed/AutoTranslate.xml",
    "AutoTranslate/Languages/PortugueseBrazilian/Keyed/AutoTranslate.xml",
    "AutoTranslate/Languages/Portuguese/Keyed/AutoTranslate.xml",
]
names = set(zipfile.ZipFile(sys.argv[1]).namelist())
if "AutoTranslate/1.7/Assemblies/RimWorldAutoTranslate.dll" not in names:
    print("NOTE: no RimWorld 1.7 build in this package (1.7 is in beta; the 1.6 build is complete)")
missing = [r for r in REQUIRED if r not in names]
for m in missing:
    print("MISSING in package:", m)
print(f"{len(names)} entries; " + ("PACKAGE INCOMPLETE" if missing else "package OK"))
sys.exit(1 if missing else 0)
