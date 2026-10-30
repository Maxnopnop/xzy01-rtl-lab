#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-4819cd56b10d418d.zip"
timeout 60s cp -- "$share/console-4819cd56b10d418d.zip" "$archive"
printf "%s  %s\n" "a959aa1df4900a9a99c525ee2b3b53328eaf142beb36cdc58a5072b228c0a05b" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="a959aa1df4900a9a99c525ee2b3b53328eaf142beb36cdc58a5072b228c0a05b":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"a959aa1df4900a9a99c525ee2b3b53328eaf142beb36cdc58a5072b228c0a05b")
PY
