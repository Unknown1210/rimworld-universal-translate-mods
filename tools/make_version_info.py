#!/usr/bin/env python3
"""Write the Windows "version information" of the helper .exe (the Details tab of its Properties): name, description, version, license.
An .exe that says what it is looks less like malware to browsers and antivirus programs than one with no information at all.
Usage: python tools/make_version_info.py version_info.txt   (then: pyinstaller --version-file version_info.txt ...)"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def build(version):
    parts = [int(p) for p in version.strip().split(".")]
    parts = (parts + [0, 0, 0, 0])[:4]
    tup = tuple(parts)
    dotted = version.strip() + (".0" if version.strip().count(".") == 1 else "")      # as written in VERSION: 0.039.0
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={tup}, prodvers={tup}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'peraquetocosta'),
      StringStruct('FileDescription', 'Universal Translate Helper - translates RimWorld mods for the Auto Translate Mods mod'),
      StringStruct('FileVersion', '{dotted}'),
      StringStruct('InternalName', 'UniversalTranslate-Helper'),
      StringStruct('LegalCopyright', 'MIT License - open source: github.com/Unknown1210/rimworld-universal-translate-mods'),
      StringStruct('OriginalFilename', 'UniversalTranslate-Helper.exe'),
      StringStruct('ProductName', 'Universal Translate Helper'),
      StringStruct('ProductVersion', '{dotted}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(argv):
    version = (ROOT / "VERSION").read_text().strip()
    text = build(version)
    if argv:
        pathlib.Path(argv[0]).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv[1:])
