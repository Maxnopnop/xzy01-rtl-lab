"""Durable bounded execution primitives. No model call at import time."""
import ast,hashlib,json,os,re,subprocess,time,datetime
from usage import usage_record
from pathlib import Path
HERE=Path(__file__).resolve().parent
BATCH=HERE.parent/'public-rag-next-v1'
BATCH_SHA='a8f24bd42a5b3d6bf3b4a7f12732dc9aa6f601347862f5538be61243677fecee'
MODELS=['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol']
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def read(p):return json.loads(Path(p).read_bytes().decode('utf-8-sig'))
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
def save_bytes(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def extract(raw):
 # Load only the two frozen definitions, never import/execute the production runner.
 raw_source=(BATCH/'A/history/rtl_lab.py').read_bytes();assert digest(raw_source)==read(BATCH/'A-lock.json')['history/rtl_lab.py'],'extractor drift'
 source=raw_source.decode('utf-8-sig');tree=ast.parse(source)
 defs=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ['LabError','extract_rtl']]
 assert len(defs)==2
 ns={'re':re};exec(compile(ast.Module(body=defs,type_ignores=[]),'<frozen_extract_rtl>','exec'),ns)
 return ns['extract_rtl'](raw,'TopModule')

def size(folder):return sum(f.stat().st_size for f in Path(folder).rglob('*') if f.is_file())
def clean_env():
 env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP'] if k in os.environ}
 root=os.environ.get('SystemRoot',r'C:\Windows');env.update(SystemRoot=root,COMSPEC=str(Path(root)/'System32/cmd.exe'),PATH=str(Path(root)/'System32')+os.pathsep+'D:/iverilog/bin');return env

def bounded_process(argv,folder,label,timeout,env):
 folder=Path(folder);out=folder/(label+'.stdout.bin');err=folder/(label+'.stderr.bin');start=time.monotonic();rc=None;reason=None;launch=None;proc=None
 save(folder/(label+'-started.json'),{'utc':utc(),'argv':argv,'timeout_seconds':timeout})
 with out.open('xb') as of,err.open('xb') as ef:
  try:
   proc=subprocess.Popen(argv,cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=of,stderr=ef,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
   while proc.poll() is None:
    if time.monotonic()-start>timeout:reason='timeout'
    elif max(out.stat().st_size,err.stat().st_size)>2097152 or size(folder)>8388608:reason='resource_limit'
    if reason:
     try:
      kill=subprocess.run([str(Path(env['SystemRoot'])/'System32/taskkill.exe'),'/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW)
      save_bytes(folder/(label+'-cleanup.stdout.bin'),kill.stdout);save_bytes(folder/(label+'-cleanup.stderr.bin'),kill.stderr)
     except Exception:proc.kill()
     try:proc.wait(timeout=3)
     except subprocess.TimeoutExpired:reason='cleanup_unknown'
     break
    time.sleep(.05)
   rc=proc.poll()
  except OSError as e:launch=type(e).__name__
  except BaseException:
   if proc is not None and proc.poll() is None:
    try:
     subprocess.run([str(Path(env['SystemRoot'])/'System32/taskkill.exe'),'/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW)
    finally:
     proc.kill()
     try:proc.wait(timeout=3)
     except subprocess.TimeoutExpired:pass
   raise
 if max(out.stat().st_size,err.stat().st_size)>2097152 or size(folder)>8388608:reason=reason or 'resource_limit'
 result={'returncode':rc,'limit_reason':reason,'launch_error':launch,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
 save(folder/(label+'-receipt.json'),result);return result

def judge(slot,folder,rtl,process=bounded_process):
 folder=Path(folder);task=slot['task'];save_bytes(folder/'dut.sv',rtl.encode())
 for dest,ext in [('reference.sv','ref.sv'),('testbench.sv','test.sv')]:
  relative=f'B/originals/dataset_spec-to-rtl/{task}_{ext}';source=(BATCH/relative).read_bytes();assert digest(source)==read(BATCH/'B-lock.json')[relative.removeprefix('B/')],'test source drift';save_bytes(folder/dest,source)
 env=clean_env();phases=[]
 for name,argv,limit in [('compile',['D:/iverilog/bin/iverilog.exe','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o','sim.vvp','dut.sv','testbench.sv','reference.sv'],15),('simulate',['D:/iverilog/bin/vvp.exe','sim.vvp'],10)]:
  assert sha(Path(argv[0]))==read(HERE/'tools-lock.json')[str(Path(argv[0]))],'tool drift'
  result=process(argv,folder,name,limit,env);phases.append(result)
  if result['launch_error'] or result['limit_reason']:return {'status':'INFRASTRUCTURE_ERROR','stage':name,'stop':True,'phases':phases}
  if result['returncode']!=0 or result['limit_reason']:return {'status':'COMPILE_ERROR' if name=='compile' else 'SIM_ERROR_OR_TIMEOUT','stage':name,'stop':False,'phases':phases}
 text=(folder/'simulate.stdout.bin').read_bytes().decode('utf-8',errors='replace');matches=[re.fullmatch(r'Mismatches: (\d+) in (\d+) samples',s) for s in text.splitlines()];matches=[(int(m[1]),int(m[2])) for m in matches if m]
 if 'TIMEOUT' in text.upper():return {'status':'RESOURCE_LIMIT','stage':'simulate','stop':True,'phases':phases,'reason':'original_tb_timeout'}
 if len(matches)!=1 or matches[0][1]==0:return {'status':'SIM_ERROR_OR_TIMEOUT','stage':'simulate','stop':False,'phases':phases,'receipt':matches}
 return {'status':'REFERENCE_PASS' if matches[0][0]==0 else 'REFERENCE_FAIL','stage':'original_test','stop':False,'phases':phases,'receipt':matches,'independent_oracle':False,'additional_sat_event':'NOT_SUPPORTED_PENDING_CONTRACT_REVIEW'}

def process_response(slot,folder,envelope,judge_fn=judge):
 base={'slot':slot['id'],'requested_model':slot['model'],'complete_http_return':envelope.get('outcome')=='HTTP_OK','usage':None}
 def outcome(status,stage,stop,**extras):return dict(base,status=status,stage=stage,stop=stop,**extras)
 if envelope.get('outcome')=='RESPONSE_SIZE_LIMIT':return outcome('RESOURCE_LIMIT','transport',True)
 if envelope.get('outcome')=='UNKNOWN':return outcome('UNKNOWN','transport',True)
 if envelope.get('outcome')!='HTTP_OK':return outcome('SERVICE_ERROR','transport',True,http_status=envelope.get('http_status'),error=envelope.get('outcome'))
 try:
  body=json.loads(envelope['body']);assert isinstance(body,dict);base['response_model']=body.get('model');base['usage']=body.get('usage');base['response_id']=body.get('id')
  if envelope.get('forced_stop'):return outcome('POSTPROCESSING_ERROR','transport_cleanup',True,reason=envelope['forced_stop'])
  if body.get('error') is not None:return outcome('SERVICE_ERROR','transport',True,upstream_error=body['error'])
  if body.get('model')!=slot.get('wire_model',slot['model']):return outcome('MODEL_ID_MISMATCH','transport',True)
  base['usage_normalized']=usage_record(body.get('usage'))
  base['reported_provider']=body.get('provider')
  if slot.get('expected_provider') and body.get('provider')!=slot['expected_provider']:return outcome('PROVIDER_ID_MISMATCH','transport',True)
  choices=body['choices'];assert isinstance(choices,list) and len(choices)==1
  c=choices[0];message=c['message'];assert message.get('role')=='assistant' and not message.get('tool_calls') and not message.get('function_call')
  raw=message.get('content');assert isinstance(raw,str) and raw.strip();base['finish_reason']=c.get('finish_reason')
 except (ValueError,KeyError,TypeError,AssertionError):return outcome('SERVICE_PROTOCOL_ERROR','transport',True)
 if len(raw.encode())>131072:return outcome('RESOURCE_LIMIT','extraction',True,reason='text_bytes_exceed_131072')
 save_bytes(Path(folder)/'model-output.txt',raw.encode())
 if c.get('finish_reason')=='length':return outcome('EXTRACTION_ERROR','extraction',False,reason='token_limit')
 if c.get('finish_reason') not in ['stop']:return outcome('SERVICE_PROTOCOL_ERROR','transport',True,reason='unexpected_finish_reason')
 try:rtl=extract(raw)
 except Exception as e:
  if hasattr(e,'status') and hasattr(e,'stage'):return outcome(e.status,e.stage,False,reason=str(e))
  raise
 verdict=judge_fn(slot,folder,rtl);return dict(base,**verdict)
