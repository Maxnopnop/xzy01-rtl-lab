#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
printf "%s  %s\n" "1c984dfd208a256b2d8fb410b8586c5b25b34abac519a59b7494bf32b1a7fa8a" console-manifest.json | sha256sum -c -
python3 - <<'PY'
import hashlib,json
from pathlib import Path
m=json.loads(Path("console-manifest.json").read_text())
for n,h in m["inputs"].items():
 if Path(n).name!=n or hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h: raise SystemExit("STOP: package hash mismatch")
PY
echo "SHARED PACKAGE VERIFIED; no EDA started"
