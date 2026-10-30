#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-47ab870fd7974a0c.zip"
timeout 60s cp -- "$share/console-47ab870fd7974a0c.zip" "$archive"
printf "%s  %s\n" "ac696ee94a353bf374435624bc7dc4a63ac5de8e1e33d2b5e86096a6fe10a3de" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="ac696ee94a353bf374435624bc7dc4a63ac5de8e1e33d2b5e86096a6fe10a3de":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"ac696ee94a353bf374435624bc7dc4a63ac5de8e1e33d2b5e86096a6fe10a3de")
PY
