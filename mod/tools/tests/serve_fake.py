"""Starts the real helper server with fake engines for several language pairs (no model download).
For the C# integration test. Output of a fake pair en->pt is "<text> (pt)"; other pairs "<text> (<tgt> from <src>)"."""
import json
import os
import sys
import tempfile

HOME = os.environ["RWTRANSLATE_HOME"]
# a tiny local "Argos index" so that installing an unavailable pair fails fast and offline (never downloads anything)
_idx = os.path.join(HOME, "fake-index.json")
json.dump([{"from_code": "en", "to_code": "pt", "package_version": "1.0", "links": ["http://127.0.0.1:9/x"]}], open(_idx, "w"))
os.environ["RWTRANSLATE_INDEX_URL"] = "file://" + _idx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "helper"))
from rwtranslate import logsetup, server  # noqa: E402
from rwtranslate.engine import set_engine  # noqa: E402
from rwtranslate.paths import models_dir  # noqa: E402


class Fake:
    def __init__(self, src, tgt):
        self.src, self.tgt = src, tgt

    def translate_batch(self, texts):
        if any("EXPLODE" in t for t in texts):
            raise RuntimeError("fake engine failure")
        if self.src == "en":
            return [f"{t} ({self.tgt})" for t in texts]
        return [f"{t} ({self.tgt} from {self.src})" for t in texts]


logsetup.setup(debug=True)
for src, tgt in [("en", "pt"), ("zh", "pt"), ("ru", "pt"), ("es", "pt"), ("pt", "en"), ("zh", "en")]:
    set_engine(src, tgt, Fake(src, tgt))
    d = models_dir() / f"{src}_{tgt}"       # pretend the model is installed
    d.mkdir(parents=True, exist_ok=True)
    (d / "ok").write_text("fake")
httpd = server.serve(0)
print("READY", flush=True)
httpd.serve_forever()
