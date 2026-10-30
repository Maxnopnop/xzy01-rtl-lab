#!/usr/bin/env bash
set -eu
share=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-main36-school-archives"
archive="$HOME/xzy01-main36-school-archives/main36-school-v1.zip"
timeout 60s cp -- "$share/main36-school-v1.zip" "$archive"
python3 - "$archive" <<'PY'
import hashlib,json,stat,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!='b5a9a138b78952b4c2ae7c639b8518ca070cf7838453efd6ef2a9cd8ff8d441b':raise SystemExit('STOP: transfer ZIP hash mismatch')
dest=Path.home()/'xzy01-main36-school-v1'
with zipfile.ZipFile(str(p)) as z:
 infos=z.infolist();names=[i.filename for i in infos]
 if len(names)!=len(set(names)) or sum(i.file_size for i in infos)>100*1024**2:raise SystemExit('Invalid archive size')
 if any(Path(n).name!=n or '\\' in n or ':' in n or n in ('.','..') for n in names):raise SystemExit('Unsafe archive path')
 if any(stat.S_ISLNK(i.external_attr>>16) for i in infos):raise SystemExit('Symlink rejected')
 lock=json.loads(z.read('bundle-lock.json'))
 if set(names)!=set(lock)|{'bundle-lock.json'}:raise SystemExit('Unexpected archive member')
 for n,h in lock.items():
  if hashlib.sha256(z.read(n)).hexdigest()!=h:raise SystemExit('Payload hash mismatch')
 dest.mkdir(parents=True,exist_ok=True)
 for n in names:
  target=dest/n
  if target.exists():
   if target.read_bytes()!=z.read(n):raise SystemExit('Existing HOME content differs; no overwrite')
  else:
   with target.open('xb') as f:f.write(z.read(n))
print('HOME VERIFIED. No EDA started: '+str(dest))
PY
python3 "$HOME/xzy01-main36-school-v1/school_main.py" check
