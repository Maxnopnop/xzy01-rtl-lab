"""Python 3.6+: authorized serial school replay; never generates RTL or retries jobs."""
import argparse,collections,hashlib,json,os,re,shutil,signal,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
STATE=Path.home().resolve()/'xzy01-rtl285-school-v1'
TOOLS=('vcs','xcelium','dc','genus')
STOP_STATES={'ENVIRONMENT_ERROR','LICENSE_ERROR','TIMEOUT','RESOURCE_LIMIT','INTERRUPTED','EVIDENCE_ERROR','UNKNOWN','RECEIPT_ERROR'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def save(p,obj):
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def verify():
 lock=read(ROOT/'package-lock.json')
 for n,h in lock.items():
  p=ROOT/n
  if '..' in Path(n).parts or p.is_symlink() or sha(p)!=h:raise ValueError('PACKAGE_CHANGED '+n)
 m=read(ROOT/'manifest.json')
 if len(m['cases'])!=285 or len(m['jobs'])!=1140:raise ValueError('COUNT_INVALID')
 return m
def check(m):
 errors=[]
 if os.name!='posix':errors.append('School Linux required')
 for name in ('tcsh','bash','python3'):
  if not shutil.which(name):errors.append('COMMAND '+name)
 paths=list(m['setups'].values())+[p for v in m['profiles'].values() for p in v['libraries']]
 for p in paths:
  if not os.access(p,os.R_OK):errors.append('UNREADABLE '+p)
 if shutil.disk_usage(str(Path.home())).free<5*1024**3:errors.append('At least 5 GiB HOME free space required')
 result={'ready':not errors,'errors':errors,'rtl':285,'jobs':1140,'concurrency':1,'automatic_retry':False,'model_calls':0,'eda_calls':0,'license':'not probed','state':str(STATE)}
 print(json.dumps(result,indent=2),flush=True);return result
def process(work,seconds=600):
 started=time.monotonic();reason=None
 with (work/'launcher.log').open('xb') as f:
  p=subprocess.Popen(['tcsh','-f','run.csh'],cwd=str(work),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   while p.poll() is None:
    files=[x for x in work.rglob('*') if x.is_file() and not x.is_symlink()]
    sizes=[x.stat().st_size for x in files]
    if time.monotonic()-started>seconds:reason='TIMEOUT'
    elif sum(sizes)>256*1024**2 or any(x.stat().st_size>16*1024**2 for x in files if x.suffix in ('.log','.rpt')):reason='RESOURCE_LIMIT'
    if reason:break
    time.sleep(.25)
  except KeyboardInterrupt:reason='INTERRUPTED'
  finally:
   if p.poll() is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  rc=p.wait()
 return {'returncode':rc,'limit':reason,'elapsed_seconds':round(time.monotonic()-started,3)}
def text(p):return p.read_text(errors='replace') if p.is_file() else ''
def classify(job,work,execution):
 rc=execution['returncode'];tool=job['tool']
 logs='\n'.join(text(work/n) for n in ('launcher.log','compile.log','simulate.log','tool.log'))
 if execution.get('limit'):return {'status':execution['limit']}
 if re.search(r'license checkout failed|unable to (?:checkout|check out)|cannot (?:checkout|check out).*license|no valid license|license.*denied|licensing error|FLEXnet Licensing error',logs,re.I):return {'status':'LICENSE_ERROR'}
 if rc in (90,91,126,127):return {'status':'ENVIRONMENT_ERROR'}
 if tool in ('vcs','xcelium'):
  if rc==92:return {'status':'COMPILE_ERROR'}
  if rc!=0:
   # Unrecognized service/launcher errors stop rather than consume all slots.
   if re.search(r'Error-\[|\*E,|\*F,|syntax error',logs,re.I):return {'status':'COMPILE_OR_SIM_ERROR'}
   return {'status':'ENVIRONMENT_ERROR'}
  output='\n'.join(text(work/'simulate.log').splitlines())
  matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$',output,re.M)
  if 'TIMEOUT' in output.upper():return {'status':'TIMEOUT'}
  if len(matches)!=1:return {'status':'RECEIPT_ERROR'}
  errors,count=map(int,matches[0]);expected=job['expected_samples']
  return {'status':('FIXED_TEST_PASS' if errors==0 else 'FUNCTION_FAIL') if count==expected else 'CHECK_COUNT_DIFFERENT','mismatches':errors,'samples':count,'expected_samples':expected}
 if rc!=0:
  if 'XZY01_SYNTH_ERROR:' in logs or re.search(r'Error:|\*E,|\*F,',logs):return {'status':'SYNTHESIS_FAILED'}
  return {'status':'ENVIRONMENT_ERROR'}
 required=['outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt']
 if text(work/'receipt.txt').strip()!='XZY01_SYNTH_V1 '+job['nonce']+' COMPLETE' or any(not (work/n).is_file() or (work/n).stat().st_size==0 for n in required):return {'status':'RECEIPT_ERROR'}
 return {'status':'COMPLETED_REVIEW_REQUIRED'}
def run_job(job):
 work=STATE/'jobs'/job['id']
 work.mkdir(parents=True,exist_ok=False)
 save(work/'reservation.json',{'job':job,'pid':os.getpid(),'time':time.time(),'package_lock_sha256':sha(ROOT/'package-lock.json')})
 for name,relative in job['inputs'].items():shutil.copyfile(str(ROOT/relative),str(work/name))
 hashes={n:sha(work/n) for n in job['inputs']};save(work/'input-lock.json',hashes)
 try:execution=process(work);result=classify(job,work,execution)
 except Exception as exc:execution={'returncode':None};result={'status':'ENVIRONMENT_ERROR','error_type':type(exc).__name__}
 save(work/'execution.json',execution)
 if any(sha(work/n)!=h for n,h in hashes.items()):result={'status':'EVIDENCE_ERROR'}
 result.update(id=job['id'],slot=job['slot'],tool=job['tool'],task=job['task'],model=job['model'],condition=job['condition'],execution=execution)
 save(work/'result.json',result)
 return result
def status(m):
 rows=[]
 for j in m['jobs']:
  d=STATE/'jobs'/j['id'];p=d/'result.json'
  rows.append(read(p) if p.exists() else {'id':j['id'],'status':'UNKNOWN_OR_RUNNING' if d.exists() else 'NOT_STARTED','tool':j['tool']})
 return {'counts':dict(collections.Counter(r['status'] for r in rows)),'tools':{t:dict(collections.Counter(r['status'] for r in rows if r['tool']==t)) for t in TOOLS},'total':1140,'rows':rows,'model_calls':0}
def run_all(m):
 if not check(m)['ready']:return 2
 STATE.mkdir(exist_ok=True)
 if (STATE/'STOP.json').exists():raise ValueError('BATCH_STOPPED; preserve STOP and request review')
 lock=STATE/'batch.lock'
 save(lock,{'pid':os.getpid(),'time':time.time()})
 try:
  paths=list(m.get('setups',{}).values())+[p for v in m.get('profiles',{}).values() for p in v['libraries']]
  environment={p:sha(Path(p)) for p in paths}
  ep=STATE/'environment.json'
  if ep.exists():
   if read(ep)['setup_and_library_sha256']!=environment:raise ValueError('School environment changed; no automatic continuation')
  else:save(ep,{'setup_and_library_sha256':environment,'python':sys.version,'host':os.uname().nodename if os.name=='posix' else 'offline-test'})
  for i,j in enumerate(m['jobs']):
   d=STATE/'jobs'/j['id']
   if d.exists():
    if not (d/'result.json').exists():raise ValueError('UNKNOWN existing attempt '+j['id'])
    if read(d/'result.json')['status'] in STOP_STATES:raise ValueError('Existing stopped attempt '+j['id'])
    continue
   r=run_job(j);print(json.dumps({'completed_ordinal':i+1,'total':1140,**r}),flush=True)
   if r['status'] in STOP_STATES:
    save(STATE/'STOP.json',r);return 2
  print(json.dumps({'complete':True,'counts':status(m)['counts'],'model_calls':0}),flush=True);return 0
 finally:lock.unlink()
def export(m):
 if (STATE/'batch.lock').exists():raise ValueError('Batch active or unknown; do not export an unstable snapshot')
 summary=status(m);records=[]
 for j in m['jobs']:
  d=STATE/'jobs'/j['id']
  if not d.exists():continue
  allowed=set(j['inputs'])|{'reservation.json','input-lock.json','execution.json','result.json','launcher.log','compile.log','simulate.log','tool_version.log','tool_path.txt','simulate.exit','receipt.txt','outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt','reports/check_design.rpt','reports/constraints.rpt'}
  for n in sorted(allowed):
   f=d/n
   if f.is_file():
    if f.is_symlink() or f.stat().st_size>16*1024**2:raise ValueError('Unsafe or oversize evidence '+str(f))
    records.append((f,'jobs/'+j['id']+'/'+n,sha(f)))
 snapshot=hashlib.sha256(json.dumps([(n,h) for f,n,h in records]).encode()).hexdigest()[:16]
 out=STATE/'exports'/snapshot
 if out.exists():
  verify_export(out);print('EXPORT '+str(out),flush=True);return out
 out.mkdir(parents=True)
 save(out/'summary.json',summary)
 if (STATE/'environment.json').exists():
  f=STATE/'environment.json';records.append((f,'environment.json',sha(f)))
 parts=[];group=[];size=0
 def part(items):
  name='returns-%03d.zip'%(len(parts)+1);zpath=out/name
  with zipfile.ZipFile(str(zpath),'x',zipfile.ZIP_DEFLATED) as z:
   for f,n,h in items:
    if sha(f)!=h:raise ValueError('Evidence changed during export')
    z.write(str(f),n)
  parts.append({'file':name,'sha256':sha(zpath),'bytes':zpath.stat().st_size})
 for entry in records:
  length=entry[0].stat().st_size
  if group and size+length>32*1024**2:part(group);group=[];size=0
  group.append(entry);size+=length
 if group:part(group)
 save(out/'return-index.json',{'package_lock_sha256':sha(ROOT/'package-lock.json'),'parts':parts,'files':{n:h for f,n,h in records},'summary_sha256':sha(out/'summary.json'),'model_calls':0})
 verify_export(out);print('EXPORT '+str(out),flush=True);return out
def verify_export(out):
 idx=read(out/'return-index.json');seen={}
 if sha(out/'summary.json')!=idx['summary_sha256']:raise ValueError('Summary changed')
 for part in idx['parts']:
  p=out/part['file']
  if sha(p)!=part['sha256']:raise ValueError('Return ZIP mismatch')
  with zipfile.ZipFile(str(p)) as z:
   for n in z.namelist():
    if n in seen:raise ValueError('Duplicate return member')
    seen[n]=hashlib.sha256(z.read(n)).hexdigest()
 if seen!=idx['files']:raise ValueError('Return contents mismatch')
 return idx
def ship(out,dest):
 verify_export(out);dest.mkdir(parents=True,exist_ok=True)
 for f in sorted(out.iterdir()):
  p=dest/f.name
  if p.exists():
   if sha(p)!=sha(f):raise ValueError('Existing different shared file; retained, no overwrite')
  else:
   with p.open('xb') as target, f.open('rb') as source:shutil.copyfileobj(source,target)
   if sha(p)!=sha(f):raise ValueError('Shared copy hash mismatch')
 verify_export(dest);print('SHARED_COPY_HASH_VERIFIED '+str(dest),flush=True)
def main():
 a=argparse.ArgumentParser();a.add_argument('action',choices=['check','run-all','status','export','ship']);a.add_argument('--source');a.add_argument('--dest');args=a.parse_args();m=verify()
 if args.action=='check':return 0 if check(m)['ready'] else 2
 if args.action=='run-all':return run_all(m)
 if args.action=='status':print(json.dumps(status(m),indent=2));return 0
 if args.action=='export':export(m);return 0
 if args.action=='ship':ship(Path(args.source),Path(args.dest));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('STOP '+str(e),flush=True);sys.exit(2)
