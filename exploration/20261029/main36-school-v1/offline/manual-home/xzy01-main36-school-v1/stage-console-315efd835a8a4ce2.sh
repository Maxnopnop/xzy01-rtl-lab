#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-315efd835a8a4ce2.zip"
timeout 60s cp -- "$share/console-315efd835a8a4ce2.zip" "$archive"
printf "%s  %s\n" "9a9df40e064df796dc5c54027c5004886813ebe289b5a43da52b365820eda0f2" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="9a9df40e064df796dc5c54027c5004886813ebe289b5a43da52b365820eda0f2":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"9a9df40e064df796dc5c54027c5004886813ebe289b5a43da52b365820eda0f2")
PY
