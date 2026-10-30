#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-7a885cf4d4c14d0c.zip"
timeout 60s cp -- "$share/console-7a885cf4d4c14d0c.zip" "$archive"
printf "%s  %s\n" "f71e0d298f1e7e14fc875a5b3509540bd12db5ffad60579a582da71dc26c9b1a" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="f71e0d298f1e7e14fc875a5b3509540bd12db5ffad60579a582da71dc26c9b1a":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"f71e0d298f1e7e14fc875a5b3509540bd12db5ffad60579a582da71dc26c9b1a")
PY
