"""One compile and at most one original-TB simulation per candidate; no repair/retry."""
import datetime,hashlib,json,os,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];sys.path.insert(0,str(R))
import rtl_lab
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
assert not (P/'calibration').exists(),'Calibration already started; never retry'
scope=read(P/'scope.json');acq=read(P/'acquisition.json');assert len(acq)==90
assert all(sha(P/r['local'])==r['sha256'] for r in acq)
env={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP','PATH') if k in os.environ}
put(P/'calibration/plan.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'max_compile_attempts':30,'max_simulate_attempts':30,'compile_timeout_seconds':15,'simulate_timeout_seconds':10,'reference_alias':'one module declaration RefModule -> TopModule in separate dut.sv; original bytes unchanged','meaning':'reference self-consistency/tool compatibility only, not independent oracle','script_sha256':sha(Path(__file__)),'scope_sha256':sha(P/'scope.json'),'tools':{'iverilog':sha(Path('D:/iverilog/bin/iverilog.exe')),'vvp':sha(Path('D:/iverilog/bin/vvp.exe'))}})
results=[]
for row in scope['tasks']:
 task=row['id'];folder=P/'calibration'/task;folder.mkdir()
 ref=(P/'originals'/row['files']['ref.sv']['path']).read_bytes();tb=(P/'originals'/row['files']['test.sv']['path']).read_bytes()
 alias,n=re.subn(rb'\bmodule\s+RefModule\b',b'module TopModule',ref,count=1);assert n==1
 (folder/'reference.sv').write_bytes(ref);(folder/'testbench.sv').write_bytes(tb);(folder/'dut.sv').write_bytes(alias)
 put(folder/'reservation.json',{'task':task,'status':'RESERVED_BEFORE_COMPILE','compile_attempt':1,'retry':0,'reference_sha256':hashlib.sha256(ref).hexdigest(),'testbench_sha256':hashlib.sha256(tb).hexdigest(),'alias_sha256':sha(folder/'dut.sv')})
 argv=['D:/iverilog/bin/iverilog.exe','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o','sim.vvp','dut.sv','testbench.sv','reference.sv']
 c=rtl_lab.run_process(argv,folder,15,env=env);put(folder/'compile.json',c)
 result={'task':task,'compile_attempts':1,'simulate_attempts':0,'status':'COMPILE_ERROR','expected_checks':None,'independent_oracle':False}
 if c['returncode']==0 and not c['timeout'] and not c.get('output_limit'):
  put(folder/'simulate-reservation.json',{'attempt':1,'retry':0})
  s=rtl_lab.run_process(['D:/iverilog/bin/vvp.exe','sim.vvp'],folder,10,env=env);put(folder/'simulate.json',s);result['simulate_attempts']=1
  matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$',s['stdout'],re.M)
  result['receipt']=matches;result['status']='SIMULATION_OR_RECEIPT_FAILURE'
  if s['returncode']==0 and not s['timeout'] and not s.get('output_limit') and 'TIMEOUT' not in s['stdout'].upper() and len(matches)==1:
   errors,count=map(int,matches[0]);result.update(mismatches=errors,observed_checks=count,status='REFERENCE_SELF_MATCH' if errors==0 and count>0 else 'REFERENCE_SELF_MISMATCH')
   if errors==0 and count>0:result['expected_checks']=count
 result['compile_log_sha256']=sha(folder/'compile.json')
 if (folder/'simulate.json').exists():result['simulate_log_sha256']=sha(folder/'simulate.json')
 put(folder/'result.json',result);results.append(result);print(task,result['status'],result['expected_checks'],flush=True)
put(P/'calibration/summary.json',{'results':results,'compile_attempts':sum(x['compile_attempts'] for x in results),'simulate_attempts':sum(x['simulate_attempts'] for x in results),'retry':0,'model_calls':0,'school_calls':0,'old_inputs_unchanged':all(sha(P/r['local'])==r['sha256'] for r in acq)})
