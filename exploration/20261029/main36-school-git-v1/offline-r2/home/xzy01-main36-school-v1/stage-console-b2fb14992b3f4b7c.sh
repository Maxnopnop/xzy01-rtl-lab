#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-b2fb14992b3f4b7c.zip"
timeout 60s cp -- "$share/console-b2fb14992b3f4b7c.zip" "$archive"
printf "%s  %s\n" "03ea2d2780c4acc985e3c3889abec8b1a0d30080845e4335b20d7e4b697c7782" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="03ea2d2780c4acc985e3c3889abec8b1a0d30080845e4335b20d7e4b697c7782":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"03ea2d2780c4acc985e3c3889abec8b1a0d30080845e4335b20d7e4b697c7782")
PY
