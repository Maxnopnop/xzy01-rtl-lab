#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
printf "%s  %s\n" "95d95ac22c53ff12c14f40bc0ea35909654227a840e43d62c6c535f5fe017b25" console-manifest.json | sha256sum -c -
python3 - <<'PY'
import hashlib,json
from pathlib import Path
m=json.loads(Path("console-manifest.json").read_text())
for n,h in m["inputs"].items():
 if Path(n).name!=n or hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h: raise SystemExit("STOP: package hash mismatch")
PY
echo "SHARED PACKAGE VERIFIED; no EDA started"
