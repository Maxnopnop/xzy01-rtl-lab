#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-1d2dea682ca84b8d.zip"
timeout 60s cp -- "$share/console-1d2dea682ca84b8d.zip" "$archive"
printf "%s  %s\n" "25fc23bb6737180a94449359f1dabac0ab6b8facc406a7a4efa4c26126b0b46f" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="25fc23bb6737180a94449359f1dabac0ab6b8facc406a7a4efa4c26126b0b46f":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"25fc23bb6737180a94449359f1dabac0ab6b8facc406a7a4efa4c26126b0b46f")
PY
