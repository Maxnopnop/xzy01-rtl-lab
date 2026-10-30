#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-b2e2993e397e4789.zip"
timeout 60s cp -- "$share/console-b2e2993e397e4789.zip" "$archive"
printf "%s  %s\n" "671478d939d3bbf0016dc22c4b88b07b1546673da93c0a3043a3f1ec8c90f1df" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="671478d939d3bbf0016dc22c4b88b07b1546673da93c0a3043a3f1ec8c90f1df":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"671478d939d3bbf0016dc22c4b88b07b1546673da93c0a3043a3f1ec8c90f1df")
PY
