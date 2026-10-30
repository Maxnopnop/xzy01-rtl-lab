#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-a5b103dc29b54bb1.zip"
timeout 60s cp -- "$share/console-a5b103dc29b54bb1.zip" "$archive"
printf "%s  %s\n" "51d9a68f8190682aacc4f7341852d3d860ae19a065d599a0177f840501d4f1c2" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="51d9a68f8190682aacc4f7341852d3d860ae19a065d599a0177f840501d4f1c2":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"51d9a68f8190682aacc4f7341852d3d860ae19a065d599a0177f840501d4f1c2")
PY
