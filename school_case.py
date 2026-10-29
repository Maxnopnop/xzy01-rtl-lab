"""Python 3.6+: manual ONE case/tool. No scheduler or model requests."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
BASE=Path.home()/'xzy01-main36-school-homefix-v1'
sys.path.insert(0,str(BASE))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verified(base):
 lock=read(base/'bundle-lock.json')
 for n,h in lock.items():
  if Path(n).name!=n or sha(base/n)!=h:raise ValueError('Bundle changed: '+n)
 return read(base/'index.json')
def checks(base,school=True):
 index=verified(base);errors=[]
 if school:
  for n in ('python3','tcsh','bash','sha256sum'):
   if not shutil.which(n):errors.append('COMMAND: '+n)
  for n in index['setups'].values():
   if not os.access(n,os.R_OK):errors.append('SETUP: '+n)
  for n in index['libraries']:
   if not os.access(n,os.R_OK):errors.append('LIBRARY: '+n)
  if os.name!='posix':errors.append('School Linux host required')
  if not (Path.home()/'xzy01-main36-git-homefix-outbox').is_dir():errors.append('LOCAL OUTBOX missing; run Git stage first')
 return {'status':'BLOCKED' if errors else 'READY_FOR_ONE_MANUAL_CASE','cases':36,'tool_cases':144,'errors':errors,'eda_calls':0,'model_calls':0,'license':'not probed'}
def chosen(index,ordinal,tool):
 matches=[r for r in index['cases'] if r['ordinal']==ordinal and r['tool']==tool]
 if len(matches)!=1:raise ValueError('Choose ordinal 1..36 and ONE of vcs/xcelium/dc/genus')
 return matches[0]
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('action',choices=['check','status','run','ship']);a.add_argument('ordinal',type=int,nargs='?');a.add_argument('tool',choices=['vcs','xcelium','dc','genus'],nargs='?');args=a.parse_args()
 if BASE!=Path.home()/'xzy01-main36-school-homefix-v1':raise ValueError('Stage the fixed bundle into HOME first')
 index=verified(BASE)
 if args.action=='check':
  result=checks(BASE);print(json.dumps(result,indent=2));return 1 if result['errors'] else 0
 if args.action=='status':
  rows=[]
  for item in index['cases']:
   work=Path.home()/'xzy01-console-single'/item['key']
   status=read(work/'console-result.json')['status'] if (work/'console-result.json').exists() else ('UNKNOWN_OR_RUNNING' if work.exists() else 'NOT_STARTED')
   rows.append(dict(ordinal=item['ordinal'],tool=item['tool'],status=status))
  print(json.dumps(rows,indent=2));return 0
 item=chosen(index,args.ordinal,args.tool)
 share=Path.home()/'xzy01-main36-git-homefix-outbox'
 if not share.is_dir():raise ValueError('Local outbox unavailable; run Git stage first')
 if args.action=='run':
  result=checks(BASE)
  if result['errors']:print(json.dumps(result,indent=2));return 2
  work=Path.home()/'xzy01-console-single'/item['key']
  if work.exists():raise ValueError('Existing school attempt: no rerun; use ship only for transfer')
 import console_stage_v3
 root=console_stage_v3.stage(BASE/item['archive'],item['archive_sha256'])
 script='run-one.sh' if args.action=='run' else 'ship-only.sh'
 command=['bash',str(root/script)]+(['run',str(share)] if args.action=='run' else [str(share)])
 if args.action=='ship':return subprocess.call(command)
 lock=BASE/'manual-one.lock'
 with lock.open('x') as f:f.write(json.dumps({'pid':os.getpid(),'ordinal':args.ordinal,'tool':args.tool}));f.flush();os.fsync(f.fileno())
 proc=None
 try:
  print('ONE SCHOOL CASE: %03d / %s. No next case is scheduled.' % (args.ordinal,args.tool),flush=True)
  proc=subprocess.Popen(command)
  return proc.wait()
 finally:
  if proc is None or proc.poll() is not None:lock.unlink()
  else:print('Interrupted while tool may still run. Lock retained; do not rerun or remove evidence.',flush=True)
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('STOP: '+str(e));sys.exit(2)
