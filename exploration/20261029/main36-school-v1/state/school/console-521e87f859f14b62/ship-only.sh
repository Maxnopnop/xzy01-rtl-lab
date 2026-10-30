#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
printf "%s  %s\n" "6b2794b450e640bc7b1fd04186aa82f2636ff18783f7fbec50aae7a6f406c846" console-manifest.json | sha256sum -c -
python3 - <<'PY'
import hashlib,json
from pathlib import Path
m=json.loads(Path("console-manifest.json").read_text())
for n,h in m["inputs"].items():
 if Path(n).name!=n or hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h: raise SystemExit("STOP: package hash mismatch")
PY
exec python3 console_school_runner_v3.py ship "$1"
