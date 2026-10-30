#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-ca8f85079ebc4b99.zip"
timeout 60s cp -- "$share/console-ca8f85079ebc4b99.zip" "$archive"
printf "%s  %s\n" "2ad6f9b7a27794338084f54253677f5b6d25f1ab1c7d3f3ab85c8ed2e17d23f6" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="2ad6f9b7a27794338084f54253677f5b6d25f1ab1c7d3f3ab85c8ed2e17d23f6":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"2ad6f9b7a27794338084f54253677f5b6d25f1ab1c7d3f3ab85c8ed2e17d23f6")
PY
