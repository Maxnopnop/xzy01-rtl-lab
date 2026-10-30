#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
printf "%s  %s\n" "7fed7e02fb6a6d614b5ebbbd99e3e1cea4b8ec367f908d3fc6214b6aba334a4f" console-manifest.json | sha256sum -c -
python3 - <<'PY'
import hashlib,json
from pathlib import Path
m=json.loads(Path("console-manifest.json").read_text())
for n,h in m["inputs"].items():
 if Path(n).name!=n or hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h: raise SystemExit("STOP: package hash mismatch")
PY
exec python3 console_school_runner_v3.py "$@"
