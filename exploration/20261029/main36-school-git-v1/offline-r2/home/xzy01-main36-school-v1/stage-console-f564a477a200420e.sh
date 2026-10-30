#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-f564a477a200420e.zip"
timeout 60s cp -- "$share/console-f564a477a200420e.zip" "$archive"
printf "%s  %s\n" "6d46f4d5e4c8d960c54cbfbee58b3edd6d27b549a8fd4154d11c677ac4684b21" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="6d46f4d5e4c8d960c54cbfbee58b3edd6d27b549a8fd4154d11c677ac4684b21":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"6d46f4d5e4c8d960c54cbfbee58b3edd6d27b549a8fd4154d11c677ac4684b21")
PY
