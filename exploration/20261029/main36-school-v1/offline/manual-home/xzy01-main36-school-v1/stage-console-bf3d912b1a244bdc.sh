#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-bf3d912b1a244bdc.zip"
timeout 60s cp -- "$share/console-bf3d912b1a244bdc.zip" "$archive"
printf "%s  %s\n" "abb2a64aadd287f5ab264dcb2586fc33a2924da0fe0c3bd01d81b73c0330a915" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="abb2a64aadd287f5ab264dcb2586fc33a2924da0fe0c3bd01d81b73c0330a915":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"abb2a64aadd287f5ab264dcb2586fc33a2924da0fe0c3bd01d81b73c0330a915")
PY
