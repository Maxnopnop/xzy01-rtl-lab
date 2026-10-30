"""Build shared ZIP and all single-case commands. No EDA/network."""
import hashlib,json,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
records=read(P/'records.json');assert len(records)==144
out=P/'outgoing'
write(out/'school_main.py',(P/'school_main.py').read_bytes())
write(out/'console_stage_v3.py',(P/'reuse/console_stage_v3.py').read_bytes())
profiles=read(P/'profiles.json')
index={'cases':[{**{k:r[k] for k in ('ordinal','slot','task','tool','model','condition','sample','expected_checks')},**{k:r['record'][k] for k in ('key','archive','archive_sha256','manifest_sha256')}} for r in records],'setups':{'vcs':'/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc','xcelium':'/usr/eelocal/cadence/xcelium2303hf/.cshrc','dc':'/usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc','genus':'/usr/eelocal/cadence/genus211/.cshrc'},'libraries':profiles['dc']['libraries']+profiles['genus']['libraries']}
write(out/'index.json',json.dumps(index,ensure_ascii=False,indent=2).encode())
lock={f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()}
write(out/'bundle-lock.json',json.dumps(lock,indent=2).encode())
archive=P/'main36-school-v1.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.iterdir()):z.write(f,f.name)
boot='''#!/usr/bin/env bash
set -eu
share=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-main36-school-archives"
archive="$HOME/xzy01-main36-school-archives/main36-school-v1.zip"
timeout 60s cp -- "$share/main36-school-v1.zip" "$archive"
python3 - "$archive" <<'PY'
import hashlib,json,stat,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!='''+repr(sha(archive))+''':raise SystemExit('STOP: transfer ZIP hash mismatch')
dest=Path.home()/'xzy01-main36-school-v1'
with zipfile.ZipFile(str(p)) as z:
 infos=z.infolist();names=[i.filename for i in infos]
 if len(names)!=len(set(names)) or sum(i.file_size for i in infos)>100*1024**2:raise SystemExit('Invalid archive size')
 if any(Path(n).name!=n or '\\\\' in n or ':' in n or n in ('.','..') for n in names):raise SystemExit('Unsafe archive path')
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
'''
write(P/'main36-school-stage-v1.sh',boot.encode())
commands=['# 36份RTL × 四工具，共144个手动单例命令\n\n每条运行一个案例、一个工具。每次等返回提示符，再执行下一条；不要整块粘贴作自动批处理。环境、许可证、超时或未知异常先停；已有尝试不能重跑。\n\n先完成共享ZIP导入及check。综合只作smoke，不构成功能/时序签核。\n']
for ordinal in range(1,37):
 r=next(r for r in records if r['ordinal']==ordinal)
 commands.append('\n## %03d %s / %s / %s / sample %s\n\n```bash\n'%(ordinal,r['task'],r['model'],r['condition'],r['sample']))
 for tool in ('vcs','xcelium','dc','genus'):commands.append('python3 "$HOME/xzy01-main36-school-v1/school_main.py" run %03d %s\n'%(ordinal,tool))
 commands.append('```\n')
write(P/'ALL_COMMANDS.md',''.join(commands).encode())
write(P/'transfer.json',json.dumps({'archive':archive.name,'archive_sha256':sha(archive),'stage':'main36-school-stage-v1.sh','stage_sha256':sha(P/'main36-school-stage-v1.sh'),'members':len(lock)+1,'school_tools_started':0},indent=2).encode())
print(json.dumps(read(P/'transfer.json')))
