"""Stage B ONLY. Requires explicit coordinator release of exact plan SHA.
Never run for preparation. Single new run, no retry/resume or model imports.
"""
import argparse,hashlib,json,subprocess,sys,time,traceback
from pathlib import Path
from transaction_relation import assess,relation
from metadata import episodes
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def verify(mapping,base):
 for name,h in mapping.items():
  p=Path(name) if Path(name).is_absolute() else base/name
  assert sha(p)==h,name
def native_trace(path):
 events=[]
 def num(t,b):return t if any(x in t.lower() for x in 'xz') else int(t,b)
 for line in path.read_text().splitlines():
  t=line.split();assert len(t)==16,'Raw row width'
  ports=[]
  for offset in (4,8,12):ports.append(dict(valid=num(t[offset],2),ready=num(t[offset+1],2),data=num(t[offset+2],16),last=num(t[offset+3],2)))
  events.append(dict(cycle=int(t[0]),phase=t[1],rst=1-int(t[2],2),offer_index=int(t[3]),s=ports[0],m=ports[1:]))
 assert len(events)==160
 for i,e in enumerate(events):assert e['cycle']==i//2 and e['phase']==('PRE' if i%2==0 else 'POST'),'Missing/duplicate phase sample'
 return events
def rows_with_ids(events,scene):
 rows=[]
 for e in events:
  if e['phase']!='PRE':continue
  epoch=int(scene in (0,4) and e['cycle']>=8)
  rows.append({**{k:e[k] for k in ('cycle','rst','s','m')},'offer_id':[epoch,e['offer_index']]})
 return rows
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--approved-plan-sha',required=True);a=ap.parse_args()
 digest=sha(R/'plan.json');assert a.approved_plan_sha==digest==read(R/'plan-lock.json')['sha256'],'Exact new plan release required'
 plan=read(R/'plan.json');assert plan['status']=='PREPARED_NOT_EXECUTED'
 verify(plan['source_hashes'],R);verify(read(R/'prior-lock.json'),ROOT)
 for tool in read(R/'tools.json')['tools']:assert sha(Path(tool['path']))==tool['sha256']
 run=R/'run-v1';assert not run.exists(),'No automatic retry/resume/overwrite'
 run.mkdir();save(run/'dispatch.json',dict(plan_sha256=digest,approved_plan_sha=a.approved_plan_sha,started_unix=time.time(),workers=1,retries=0))
 started=time.monotonic();results=[];calls=dict(ir=0,compile=0,sim=0)
 def budget():
  assert time.monotonic()-started<1800,'Wall budget exhausted'
  assert sum(p.stat().st_size for p in run.rglob('*') if p.is_file())<250*1024*1024,'Disk budget exhausted'
 def invoke(folder,name,cmd,timeout,category):
  budget();assert calls[category]<11;calls[category]+=1
  receipt=dict(argv=cmd,cwd=str(folder),timeout_seconds=timeout,executable_sha256=sha(Path(cmd[0])),reserved=True,started_unix=time.time())
  save(folder/(name+'-started.json'),receipt)
  t=time.monotonic()
  try:
   p=subprocess.run(cmd,cwd=folder,capture_output=True,timeout=timeout);stdout,stderr=p.stdout,p.stderr
   receipt.update(returncode=p.returncode,timeout=False)
  except subprocess.TimeoutExpired as e:
   stdout,stderr=e.stdout or b'',e.stderr or b'';receipt.update(returncode=None,timeout=True)
  (folder/(name+'.stdout.bin')).write_bytes(stdout);(folder/(name+'.stderr.bin')).write_bytes(stderr)
  receipt.update(seconds=time.monotonic()-t);save(folder/(name+'-receipt.json'),receipt)
  assert receipt['returncode']==0 and not receipt['timeout'],name+' infrastructure failure'
 status='INTERRUPTED_UNKNOWN_NO_RETRY'
 try:
  for case in plan['cases']:
   budget();folder=run/case['id'];folder.mkdir();save(folder/'case.json',case)
   if case.get('skip'):
    row=dict(id=case['id'],observed=case['expected'],matched=True,executed=False,reason='Predeclared missing reset policy, not an executed calibration');save(folder/'result.json',row);results.append(row);continue
   invoke(folder,'ir',[sys.executable,str(R/'ir_worker.py'),'--case',case['id'],'--out',str(folder)],30,'ir')
   binary=folder/'sim.vvp'
   cmd=['D:/iverilog/bin/iverilog.exe','-g2012','-s','tb']+[f'-Ptb.{name}={case[key]}' for name,key in [('KIND','kind'),('SCENE','scene'),('FAULT','fault'),('LATENCY','latency')]]+['-o',str(binary),str(R/'development.v'),str(R/'tb.v')]
   invoke(folder,'compile',cmd,15,'compile');invoke(folder,'sim',['D:/iverilog/bin/vvp.exe',str(binary)],10,'sim')
   events=native_trace(folder/'trace.txt');save(folder/'native-normalized-events.json',events)
   raw_rows=rows_with_ids(events,case['scene']);save(folder/'native-pre-full.json',raw_rows)
   sample_rows=[r for r in raw_rows if r['cycle']!=case.get('drop_rtl_cycle',-1)];save(folder/'native-assessment-view.json',sample_rows)
   ir=assess(read(folder/'ir-pre.json'),episodes(case['scene']));rtl=assess(sample_rows,episodes(case['scene']));intent=relation(ir,rtl)
   save(folder/'ir-assessment.json',ir);save(folder/'rtl-assessment.json',rtl);save(folder/'intent-assessment.json',intent)
   phase_identity=None
   if case['id'] in ('01_same_mapping','07_partial_delivery_reset'):
    ir_events=read(folder/'ir-events.json');differences=[]
    for x,y in zip(ir_events,events):
     o=x['outputs'];p=y['s'];ms=y['m']
     actual=[p['ready']]+[ms[i][key] for i in range(2) for key in ('valid','data','last')]
     expected=[o['s_ready']]+[o[f'm_{field}{i}'] for i in range(2) for field in ('valid','data','last')]
     if actual!=expected:differences.append(dict(cycle=x['cycle'],phase=x['phase'],expected=expected,actual=actual))
    phase_identity=dict(compared_events=160,differences=differences);save(folder/'same-mapping-phase-identity.json',phase_identity)
   observed=dict(ir_spec=ir['spec']['status'],rtl_spec=rtl['spec']['status'],intent=intent['status'])
   matched=observed==case['expected'] and (not case.get('required_rtl_category') or case['required_rtl_category'] in rtl['spec'].get('counts',{})) and (phase_identity is None or not phase_identity['differences'])
   row=dict(id=case['id'],observed=observed,expected=case['expected'],matched=matched,executed=True);save(folder/'result.json',row);results.append(row)
   if not matched:raise AssertionError('Predeclared expectation mismatch: '+case['id'])
  verify(plan['source_hashes'],R);verify(read(R/'prior-lock.json'),ROOT)
  status='COMPLETED_EXPECTATIONS_MATCHED'
 except Exception as exc:
  status='STOPPED_PRESERVE_NO_RETRY';save(run/'stop.json',dict(error=repr(exc),traceback=traceback.format_exc(),automatic_retry=False))
 finally:
  summary=dict(status=status,denominator=12,results=results,pending=[c['id'] for c in plan['cases'] if c['id'] not in {r['id'] for r in results}],actual_calls=calls,model_calls=0,seconds=time.monotonic()-started,plan_sha256=digest,new_external_task_release=False)
  save(run/'summary.json',summary);save(run/'evidence-lock.json',{p.relative_to(run).as_posix():sha(p) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})
 print(json.dumps(summary));return 0 if status=='COMPLETED_EXPECTATIONS_MATCHED' else 1
if __name__=='__main__':raise SystemExit(main())
