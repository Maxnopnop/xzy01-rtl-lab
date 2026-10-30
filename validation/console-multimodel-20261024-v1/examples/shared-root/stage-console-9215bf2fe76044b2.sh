#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-9215bf2fe76044b2.zip"
timeout 60s cp -- "$share/console-9215bf2fe76044b2.zip" "$archive"
printf "%s  %s\n" "39ffe8426078ca6e50db06cb989054a83db8f247a4b9de0cccd87749d2d2801d" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="39ffe8426078ca6e50db06cb989054a83db8f247a4b9de0cccd87749d2d2801d":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"39ffe8426078ca6e50db06cb989054a83db8f247a4b9de0cccd87749d2d2801d")
PY
