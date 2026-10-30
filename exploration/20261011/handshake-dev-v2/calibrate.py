"""One finite dev-only native run. No model/network/production adapter."""
import hashlib,json,subprocess,time
from pathlib import Path
from checker import check
from fixtures import build
from parse_trace import parse_trace
R=Path(__file__).resolve().parent
CASES=[
 ('shared_reset_flush',0,0,0,'PASS',None),
 ('shared_reset_stale',0,0,1,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL'),
 ('queue_reset_flush',1,0,0,'PASS',None),
 ('queue_reset_stale',1,0,1,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL'),
 ('queue_continuous_independent',1,1,0,'PASS',None),
 ('legal_same_edge',2,2,0,'PASS',None),
 ('legal_valid_before_accept',3,3,0,'PASS',None),
 ('illegal_consume_before_accept',4,2,0,'FUNCTION_FAIL','UNEXPECTED_TRANSACTION')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def plan(scene):
 if scene==0:return [dict(beats=[[0x11+i,int(i==2)] for i in range(3)],termination='reset'),dict(beats=[[0xa1+i,int(i==2)] for i in range(3)],termination='drain')]
 return [dict(beats=[[0x20+i,int(i==7)] for i in range(8)] if scene==1 else [[0x51,1]],termination='drain')]
def main():
 out=R/'calibration-v2';assert not out.exists(),'Never retry/overwrite original run';out.mkdir()
 source_names=['checker.py','fixtures.py','parse_trace.py','calibrate.py','development.v','tb.v','CONTRACT.md','PROTOCOL.md']
 sources={n:sha(R/n) for n in source_names};save(out/'source-lock.json',sources)
 started=json.loads((R/'preparation.json').read_text())['start_unix'];fixture_results=[];native=[]
 fs=build();assert len(fs)==8 and len(CASES)==8
 for f in fs:
  folder=out/'fixtures'/f['name'];folder.mkdir(parents=True);save(folder/'input.json',f)
  v=check(f['rows'],f['episodes']);save(folder/'verdict.json',v)
  row=dict(name=f['name'],expected=f['expected_status'],observed=v['status'],category=f['expected_category'],matched=v['status']==f['expected_status'] and (not f['expected_category'] or f['expected_category'] in v.get('counts',{})))
  fixture_results.append(row)
 for name,kind,scene,fault,expected,category in CASES:
  assert time.time()-started<3600 and sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<250*1024*1024
  folder=out/'rtl'/name;folder.mkdir(parents=True)
  row=dict(name=name,parameters=dict(KIND=kind,SCENE=scene,FAULT=fault),expected=expected,expected_category=category,commands=[],source_plan=plan(scene))
  cmds=[['D:/iverilog/bin/iverilog.exe','-g2012','-s','tb',f'-Ptb.KIND={kind}',f'-Ptb.SCENE={scene}',f'-Ptb.FAULT={fault}','-o',str(folder/'sim.vvp'),str(R/'development.v'),str(R/'tb.v')],['D:/iverilog/bin/vvp.exe',str(folder/'sim.vvp')]]
  for i,cmd in enumerate(cmds):
   t=time.monotonic()
   try:
    p=subprocess.run(cmd,cwd=folder,capture_output=True,timeout=15 if i==0 else 10)
    stdout,stderr=p.stdout,p.stderr;rc=p.returncode;timeout=False
   except subprocess.TimeoutExpired as e:stdout,stderr=e.stdout or b'',e.stderr or b'';rc=None;timeout=True
   (folder/f'{i}.stdout.bin').write_bytes(stdout);(folder/f'{i}.stderr.bin').write_bytes(stderr)
   row['commands'].append(dict(argv=cmd,returncode=rc,timeout=timeout,seconds=time.monotonic()-t,executable_sha256=sha(Path(cmd[0]))))
   if timeout or rc:break
  if len(row['commands'])==2 and all(c['returncode']==0 for c in row['commands']):
   try:
    trace=parse_trace(folder/'trace.txt');save(folder/'normalized-trace.json',trace)
    v=check(trace,row['source_plan']);save(folder/'verdict.json',v)
    row.update(observed=v['status'],counts=v.get('counts',{}),matched=v['status']==expected and (not category or category in v.get('counts',{})))
   except Exception as e:row.update(observed='TRACE_PARSE_ERROR',message=repr(e),matched=False)
  else:row.update(observed='INFRA_ERROR',matched=False)
  save(folder/'receipt.json',row);native.append(row);print(json.dumps(dict(name=name,observed=row['observed'],matched=row['matched'])))
 summary=dict(kind='SAME_AUTHOR_DEVELOPMENT_ONLY',fixture_denominator=8,native_denominator=8,fixtures=fixture_results,native=native,all_expected=all(x['matched'] for x in fixture_results+native),new_model_calls=0,source_sha256=sources,compile_count=sum(bool(x['commands']) for x in native),sim_count=sum(len(x['commands'])==2 for x in native),default_regression='Not rerun; inherited frozen v1 exit1, no production runner/FSM edits')
 save(out/'summary.json',summary);assert sources=={n:sha(R/n) for n in source_names}
 save(out/'evidence-lock.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-lock.json'})
 print(json.dumps(fixture_results));return 0 if summary['all_expected'] else 1
if __name__=='__main__':raise SystemExit(main())
