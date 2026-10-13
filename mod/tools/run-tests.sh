#!/usr/bin/env bash
# Compile-checks the mod against API stubs and runs the C# integration test against the real Python helper.
# Needs: mono-mcs + mono-devel (apt install mono-mcs mono-devel), python3. Works on Linux/macOS.
# Does NOT need RimWorld. It cannot prove the real game API matches (the real build checks that).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mktemp -d)"
export RWTRANSLATE_HOME="$(mktemp -d)"
python3 "$HERE/tools/check_keys.py"
export AT_MOD_DIR="$HERE"
python3 -I - "$HERE" <<'PY'
# a cache file written by the helper's bulk translation: the C# test must be able to read it
import sys
sys.path.insert(0, sys.argv[1] + "/../helper")
from rwtranslate import bulk
bulk.write_cache("pt", "py.written", {bulk.normalize("A long\n      description   with spaces"): "Uma descrição longa"})
PY
mcs -r:System.Xml.Linq -resource:"$HERE/Languages/English/Keyed/AutoTranslate.xml,AutoTranslate.English.xml" -out:"$OUT/harness.exe" -langversion:7 -nowarn:0649,0169,0414 $(find "$HERE/Source" "$HERE/tools/stubs" "$HERE/tools/tests" -name '*.cs')
python3 -I "$HERE/tools/tests/serve_fake.py" > "$OUT/serve.out" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
for _ in $(seq 1 50); do grep -q READY "$OUT/serve.out" && break; sleep 0.2; done
mono "$OUT/harness.exe"
