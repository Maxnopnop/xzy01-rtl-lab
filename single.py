"""Python3.6: one user-authorized Xcelium replay, only after the main batch finishes."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=Path.home().resolve()/'xzy01-rtl285-git-v2'
MAIN=Path.home().resolve()/'xzy01-rtl285-school-v2'
STATE=Path.home().resolve()/'xzy01-rtl285-six-replay-v1'
PIN={'package-lock.json':'5459c680a34426bd9aad11fccf14c05d2c584f69e6477f255fa8eccac5aa8655','runner.py':'fc0986ad90cc06dff9b5575de25af28cb92aaecc5ea19f274eb465c4168ec3ee'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def load():
 for n,h in read(HERE/'wrapper-lock.json').items():
  if Path(n).name!=n or sha(HERE/n)!=h:raise ValueError('Wrapper changed '+n)
 for n,h in PIN.items():
  if sha(PARENT/n)!=h:raise ValueError('Wrong frozen parent '+n)
 spec=importlib.util.spec_from_file_location('frozen_school',PARENT/'runner.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
 m=r.verify();job=next(j for j in m['jobs'] if j['id']=='002-xcelium')
 if job['slot']!='ds19freshv2-002' or job['tool']!='xcelium':raise ValueError('Wrong sixth job')
 r.STATE=STATE
 old_status=r.status
 def status(subset):
  result=old_status(subset);result.update(total=1,attempt='sixth-explicit-replay-v1',separate_from_mainline=True);return result
 r.status=status
 return r,m,job
def gate(m):
 if (MAIN/'batch.lock').exists():raise ValueError('Main batch active or unknown; wait, do not remove lock')
 if (MAIN/'STOP.json').exists():raise ValueError('Main batch stopped; remaining jobs not cleared')
 hashes={};missing=[]
 for j in m['jobs']:
  p=MAIN/'jobs'/j['id']/'result.json'
  if not p.is_file():missing.append(j['id']);continue
  x=read(p)
  if any(x.get(k)!=j[k] for k in ('id','slot','tool','task','model','condition')):raise ValueError('Main result identity changed '+j['id'])
  if x.get('status') in ('UNKNOWN','UNKNOWN_OR_RUNNING','NOT_STARTED'):missing.append(j['id'])
  hashes[str(p)]=sha(p)
 if missing:raise ValueError('Main batch incomplete: %d missing/unresolved; first=%s'%(len(missing),missing[0]))
 if len(hashes)!=1140:raise ValueError('Expected all 1140 original attempt records')
 return hashes
def verify_old(hashes):
 if any(sha(Path(n))!=h for n,h in hashes.items()):raise ValueError('Original result changed during separate replay')
def school_ready(m):
 if os.name!='posix' or not shutil.which('tcsh'):raise ValueError('School Linux/tcsh required')
 if not os.access(m['setups']['xcelium'],os.R_OK):raise ValueError('Xcelium setup unreadable')
def execute(r,m,job):
 hashes=gate(m)
 if STATE.exists():raise ValueError('Separate replay already reserved; never run again, use export or ship only')
 school_ready(m)
 STATE.mkdir(exist_ok=False)
 r.save(STATE/'authorization.json',{'user_authorized_single_eda_replay':True,'job_id':job['id'],'prior_failure_preserved':True,'model_calls':0,'max_new_eda_jobs':1})
 r.save(STATE/'parent-result-lock.json',hashes)
 result=r.run_job(job)
 verify_old(hashes)
 r.save(STATE/'old-results-preserved.json',{'checked':1140,'unchanged':True})
 print(json.dumps(result),flush=True)
 r.export({'jobs':[job]})
 return 0 if result['status']=='FIXED_TEST_PASS' else 1
def main():
 a=argparse.ArgumentParser();a.add_argument('action',choices=['check','run','export','ship','copy']);a.add_argument('--source');a.add_argument('--dest');args=a.parse_args();r,m,job=load()
 if args.action=='check':gate(m);print('READY: one separate 002-xcelium attempt; model_calls=0');return 0
 if args.action=='run':return execute(r,m,job)
 if args.action=='export':r.export({'jobs':[job]});return 0
 if args.action=='copy':r.ship(Path(args.source),Path(args.dest));return 0
 if not (STATE/'jobs'/job['id']/'result.json').is_file():raise ValueError('No completed replay result to ship')
 out=r.export({'jobs':[job]});share=Path.home()/'tsclient/FYP'
 if not share.is_dir():raise ValueError('Share unavailable; HOME export retained')
 try:return subprocess.call([sys.executable,str(HERE/'single.py'),'copy','--source',str(out),'--dest',str(share/'rtl285-six-replay-v1'/out.name)],timeout=120)
 except subprocess.TimeoutExpired:print('TRANSFER_TIMEOUT; keep HOME evidence; do not rerun EDA');return 2
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('STOP '+str(e),flush=True);sys.exit(2)
