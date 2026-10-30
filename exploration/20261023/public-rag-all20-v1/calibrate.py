"""One finite all20 original-reference harness smoke, no model APIs or retries."""
from pathlib import Path
import json,hashlib,datetime,os,time,subprocess,sys
sys.dont_write_bytecode=True
from receipt_parser import assess
P=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes().decode('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,obj):
 p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def durable(p,obj):
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
def size(folder):return sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
def main():
 seal=read(P/'pre-execution-seal.json');lock=read(P/'pre-execution-lock.json');assert sha(P/'pre-execution-lock.json')==seal['lock_sha256']
 assert all(sha(P/k)==h for k,h in lock.items())
 plan=read(P/'calibration-plan.json');run=P/'calibration-v1';run.mkdir() # Exclusive no-resume, no-retry.
 durable(run/'started.json',{'utc':utc(),'pre_execution_lock_sha256':seal['lock_sha256'],'plan_sha256':sha(P/'calibration-plan.json'),'model_calls':0})
 env=read(P/'calibration-environment.json')['values'];limits=plan['limits'];global_start=time.monotonic();results=[];compile_count=sim_count=0
 for task in plan['task_order']:
  if time.monotonic()-global_start>=limits['total_seconds']:break
  folder=run/task;folder.mkdir()
  for name,source in [('reference.sv',P/'originals/dataset_spec-to-rtl'/f'{task}_ref.sv'),('testbench.sv',P/'originals/dataset_spec-to-rtl'/f'{task}_test.sv'),('reference_alias.sv',P/'reference-aliases'/f'{task}.sv')]:
   assert sha(source)==plan['input_bindings'][source.relative_to(P).as_posix()];(folder/name).write_bytes(source.read_bytes())
  phases=[]
  commands=[('compile',['D:/iverilog/bin/iverilog.exe','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o','sim.vvp','reference_alias.sv','testbench.sv','reference.sv'],limits['per_compile_seconds']),('simulate',['D:/iverilog/bin/vvp.exe','sim.vvp'],limits['per_sim_seconds'])]
  for name,argv,timeout in commands:
   assert sha(Path(argv[0]))==plan['tools'][str(Path(argv[0]))]
   if name=='compile':compile_count+=1;assert compile_count<=limits['compile']
   else:sim_count+=1;assert sim_count<=limits['simulate']
   durable(folder/(name+'-started.json'),{'utc':utc(),'stage':name,'argv':argv,'timeout_seconds':timeout})
   start=time.monotonic();reason=None;launch_error=None;rc=None;cleanup=None
   out=folder/(name+'.stdout.bin');err=folder/(name+'.stderr.bin')
   with out.open('xb') as of,err.open('xb') as ef:
    try:
     proc=subprocess.Popen(argv,cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=of,stderr=ef,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
     while proc.poll() is None:
      if time.monotonic()-start>timeout:reason='phase_timeout'
      elif time.monotonic()-global_start>limits['total_seconds']:reason='total_timeout'
      elif max(out.stat().st_size,err.stat().st_size)>limits['stdout_or_stderr_limit_bytes']:reason='output_limit'
      elif size(folder)>limits['max_per_case_disk_bytes'] or size(run)>limits['max_total_disk_bytes']:reason='disk_limit'
      if reason:
       try:
        kr=subprocess.run([str(Path(env['SystemRoot'])/'System32/taskkill.exe'),'/PID',str(proc.pid),'/T','/F'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW);cleanup={'returncode':kr.returncode};(folder/(name+'-cleanup.stdout.bin')).write_bytes(kr.stdout);(folder/(name+'-cleanup.stderr.bin')).write_bytes(kr.stderr)
       except Exception as e:cleanup={'error_type':type(e).__name__};proc.kill()
       try:proc.wait(timeout=3)
       except subprocess.TimeoutExpired:reason='cleanup_unknown'
       break
      time.sleep(.05)
     rc=proc.poll()
    except OSError as e:launch_error={'type':type(e).__name__,'errno':e.errno}
   if max(out.stat().st_size,err.stat().st_size)>limits['stdout_or_stderr_limit_bytes']:reason=reason or 'output_limit'
   if size(folder)>limits['max_per_case_disk_bytes'] or size(run)>limits['max_total_disk_bytes']:reason=reason or 'disk_limit'
   phase={'stage':name,'returncode':rc,'limit_reason':reason,'launch_error':launch_error,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(out),'stderr_sha256':sha(err),'cleanup':cleanup}
   phases.append(phase);write(folder/(name+'-receipt.json'),phase)
   if rc!=0 or reason or launch_error:break
  output=(folder/'simulate.stdout.bin').read_bytes().decode('utf-8',errors='replace') if (folder/'simulate.stdout.bin').exists() else ''
  result=assess(output,phases);result.update(task=task,phases=phases);write(folder/'assessment.json',result);results.append(result)
  write(run/'progress.json',{'completed':len(results),'compile_attempts':compile_count,'sim_attempts':sim_count,'results':results})
  print(json.dumps({'task':task,'status':result['status'],'receipt':result['original_receipt']}),flush=True)
  if result['status']!='HARNESS_SMOKE_PASS':break
 summary={'utc':utc(),'status':'HARNESS_CALIBRATION_COMPLETE' if len(results)==20 and all(r['status']=='HARNESS_SMOKE_PASS' for r in results) else 'STOPPED_NO_RETRY','compile_attempts':compile_count,'sim_attempts':sim_count,'completed_tasks':len(results),'not_started_tasks':plan['task_order'][len(results):],'model_calls':0,'reference_independence':False,'elapsed_seconds':time.monotonic()-global_start,'results':results}
 write(run/'summary.json',summary)
 write(run/'evidence-lock.json',{f.relative_to(run).as_posix():sha(f) for f in sorted(run.rglob('*')) if f.is_file()})
 return 0 if summary['status']=='HARNESS_CALIBRATION_COMPLETE' else 1
if __name__=='__main__':raise SystemExit(main())
