"""`rwtranslate diagnostics`: bundle logs + environment into one zip to attach to a bug report.
Never includes the auth token."""
import datetime
import json
import zipfile

from .logsetup import environment
from .paths import data_dir, logs_dir


def make_bundle(out_dir=None):
    out_dir = out_dir or data_dir()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = out_dir / f"rwtranslate-diagnostics-{stamp}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(logs_dir().rglob("*")):
            if f.is_file():
                z.write(f, "logs/" + f.relative_to(logs_dir()).as_posix())
        z.writestr("environment.json", json.dumps(environment(), indent=2, ensure_ascii=False))
        cache = data_dir() / "cache"
        if cache.exists():  # sizes only, not content
            z.writestr("cache-summary.txt", "\n".join(
                f"{p.relative_to(cache).as_posix()}  {p.stat().st_size} bytes" for p in sorted(cache.rglob("*.json"))))
    return dest
