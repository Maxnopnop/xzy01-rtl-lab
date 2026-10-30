"""Finite local offline calibration. No model adapter/import or external source."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
from checker import check
from fixtures import build
R=Path(__file__).resolve().parent
CASES=[
 ('legal_no_added_delay',0,0,0,'PASS',None),
 ('legal_three_cycle_delay_changed_idle',3,1,0,'PASS',None),
 ('legal_three_cycle_delay_unknown_idle',3,2,0,'PASS',None),
 ('loss_final_consumer0',0,0,1,'FUNCTION_FAIL','MISSING_TRANSACTION'),
 ('duplicate_consumer0',0,0,2,'FUNCTION_FAIL','UNEXPECTED_TRANSACTION'),
 ('stall_data_break',0,0,3,'FUNCTION_FAIL','BACKPRESSURE_FAIL'),
 ('stall_valid_break',0,0,4,'FUNCTION_FAIL','BACKPRESSURE_FAIL'),
 ('stall_last_break',0,0,5,'FUNCTION_FAIL','BACKPRESSURE_FAIL'),
 ('data_corrupt',0,0,6,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL'),
 ('never_input_ready',0,0,7,'FUNCTION_FAIL','LIVENESS_FAIL')]
SOURCE_PLAN=[dict(beats=[[0x11,0],[0x22,1],[0x11,1],[0x80,0],[0xfe,1]],termination='drain')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def parse_trace(p):
 def number(x,base):return x if any(c in x.lower() for c in 'xz') else int(x,base)
 rows=[]
 for line in p.read_text().splitlines():
  t=line.split()
  if len(t)!=14:raise ValueError('Bad trace row width')
  endpoints=[]
  for i in (2,6,10):endpoints.append(dict(valid=number(t[i],2),ready=number(t[i+1],2),data=number(t[i+2],16),last=number(t[i+3],2)))
  rows.append(dict(cycle=int(t[0]),rst=number(t[1],2),s=endpoints[0],m=endpoints[1:]))
 return rows
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args();out=Path(args.out).resolve()
 assert out.is_relative_to(R) and not out.exists(),'Use a new own run; no overwrite'
 out.mkdir();start=time.monotonic()
 source_files=['checker.py','fixtures.py','calibrate.py','development_broadcast.v','tb.v','CONTRACT.md','test_checker.py']
 source_lock={n:sha(R/n) for n in source_files};save(out/'source-lock.json',source_lock)
 trace_results=[];rtl_results=[]
 for f in build():
  result=check(f['rows'],f['episodes']);matched=result['status']==f['expected_status'] and (not f['expected_category'] or f['expected_category'] in result.get('counts',{}))
  folder=out/'fixtures'/f['name'];folder.mkdir(parents=True);save(folder/'input.json',f);save(folder/'result.json',result)
  trace_results.append(dict(name=f['name'],expected=f['expected_status'],observed=result['status'],expected_category=f['expected_category'],matched=matched))
 assert len(trace_results)<=24 and len(CASES)<=10
 for name,latency,invalid,mode,expected,category in CASES:
  assert time.monotonic()-start<3600 and sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<250*1024*1024
  folder=out/'rtl'/name;folder.mkdir(parents=True)
  row=dict(name=name,parameters=dict(LATENCY=latency,INVALID_STYLE=invalid,MODE=mode),expected_status=expected,expected_category=category,commands=[])
  commands=[['D:/iverilog/bin/iverilog.exe','-g2012','-s','tb',f'-Ptb.LATENCY={latency}',f'-Ptb.INVALID_STYLE={invalid}',f'-Ptb.MODE={mode}','-o',str(folder/'sim.vvp'),str(R/'development_broadcast.v'),str(R/'tb.v')],['D:/iverilog/bin/vvp.exe',str(folder/'sim.vvp')]]
  for i,cmd in enumerate(commands):
   before=time.monotonic()
   try:
    p=subprocess.run(cmd,cwd=folder,capture_output=True,timeout=15 if i==0 else 10)
    (folder/f'{i}.stdout.bin').write_bytes(p.stdout);(folder/f'{i}.stderr.bin').write_bytes(p.stderr)
    row['commands'].append(dict(argv=cmd,returncode=p.returncode,timeout=False,seconds=time.monotonic()-before,executable_sha256=sha(Path(cmd[0]))))
    if p.returncode:break
   except subprocess.TimeoutExpired as e:
    (folder/f'{i}.stdout.bin').write_bytes(e.stdout or b'');(folder/f'{i}.stderr.bin').write_bytes(e.stderr or b'')
    row['commands'].append(dict(argv=cmd,returncode=None,timeout=True,seconds=time.monotonic()-before));break
  if len(row['commands'])==2 and all(x['returncode']==0 for x in row['commands']):
   try:
    rows=parse_trace(folder/'trace.txt');save(folder/'normalized-trace.json',rows)
    result=check(rows,SOURCE_PLAN);save(folder/'verdict.json',result)
    row['observed_status']=result['status'];row['observed_categories']=list(result.get('counts',{}));row['matched']=result['status']==expected and (not category or category in row['observed_categories'])
   except Exception as e:row.update(observed_status='TRACE_PARSE_ERROR',message=repr(e),matched=False)
  else:row.update(observed_status='INFRA_ERROR',matched=False)
  save(folder/'receipt.json',row);rtl_results.append(row)
  print(json.dumps({k:row[k] for k in ['name','expected_status','observed_status','matched']}))
 summary=dict(kind='HANDSHAKE_DEVELOPMENT_CALIBRATION_ONLY',fixture_denominator=len(trace_results),rtl_denominator=len(rtl_results),trace_fixtures=trace_results,rtl=rtl_results,all_expected_outcomes=all(x['matched'] for x in trace_results+rtl_results),new_model_calls=0,source_plan=SOURCE_PLAN,source_sha256=source_lock,seconds=time.monotonic()-start,tool_compile=sum(len(x['commands'])>0 for x in rtl_results),tool_simulate=sum(len(x['commands'])>1 for x in rtl_results),limitations=['Original same-author synthetic development, not external heldout or model improvement','Bounded80-cycle trace/8-cycle fair drain, no unbounded liveness','Native tests initial sync reset only; mid-reset semantic witness is hand trace','No IR/prompt/production runner integration or R7 rescoring'])
 save(out/'summary.json',summary)
 assert source_lock=={n:sha(R/n) for n in source_files},'Active calibration source changed'
 save(out/'evidence-lock.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-lock.json'})
 return 0 if summary['all_expected_outcomes'] else 1
if __name__=='__main__':raise SystemExit(main())
