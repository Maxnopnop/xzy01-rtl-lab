"""Durable bounded execution primitives. No model call at import time."""
import ast,hashlib,json,os,re,subprocess,time,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
BATCH=HERE.parent/'public-rag-all20-v1'
BATCH_SHA='72094112b5c0f6b72e920ad8d362c78ee5e302ee758b1e2de90c7c120b062d39'
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
def verify_batch():
 assert sha(BATCH/'packet-lock.json')==BATCH_SHA,'batch lock changed'
 assert all(sha(BATCH/k)==v for k,v in read(BATCH/'packet-lock.json').items()),'batch drift'
 slots=read(BATCH/'slots.json');assert len(slots)==240 and len({s['id'] for s in slots})==240
 return slots

def extract(raw):
 # Load only the two frozen definitions, never import/execute the production runner.
 source=(BATCH/'A/history/rtl_lab.py').read_bytes().decode('utf-8-sig');tree=ast.parse(source)
 defs=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ['LabError','extract_rtl']]
 assert len(defs)==2
 ns={'re':re};exec(compile(ast.Module(body=defs,type_ignores=[]),'<frozen_extract_rtl>','exec'),ns)
 return ns['extract_rtl'](raw,'TopModule')

class Ledger:
 def __init__(self,root,slots,mode):
  self.root=Path(root);self.slots=slots;self.mode=mode;self.root.mkdir(parents=True,exist_ok=True)
  (self.root/'reservations').mkdir(exist_ok=True);(self.root/'results').mkdir(exist_ok=True)
  if not (self.root/'identity.json').exists():save(self.root/'identity.json',{'batch_sha256':BATCH_SHA,'mode':mode,'start_epoch':time.time(),'slot_ids':[s['id'] for s in slots]})
  identity=read(self.root/'identity.json');assert identity['mode']==mode and identity['batch_sha256']==BATCH_SHA and identity['slot_ids']==[s['id'] for s in slots]
 def lock(self):save(self.root/'exclusive.lock',{'pid':os.getpid(),'utc':utc()})
 def unlock(self):(self.root/'exclusive.lock').unlink()
 def stop(self,reason):
  if not (self.root/'STOP.json').exists():save(self.root/'STOP.json',{'utc':utc(),'reason':reason})
 def reservations(self):return list((self.root/'reservations').glob('*.json'))
 def recover(self):
  pending=[p.stem for p in self.reservations() if not (self.root/'results'/p.name).exists()];unknown=[]
  if pending:self.stop('UNFINISHED_RESERVATION_NO_RESEND')
  for sid in pending:
   response=self.root/'jobs'/sid/'transport-response.json'
   try:
    envelope=read(response);body=json.loads(envelope.get('body','{}'))
    if envelope.get('outcome')=='HTTP_OK':
     slot=next(s for s in self.slots if s['id']==sid)
     self.finish(slot,{'slot':sid,'status':'RECOVERY_RESPONSE_UNPROCESSED','stage':'recovery','stop':True,'complete_http_return':True,'usage':body.get('usage') if isinstance(body,dict) else None,'mode':self.mode})
    else:unknown.append(sid)
   except (OSError,ValueError,TypeError):unknown.append(sid)
  return unknown
 def reserve(self,slot,request_sha):
  assert not (self.root/'STOP.json').exists(),'batch stopped'
  assert not self.recover(),'unknown reservation'
  assert len(self.reservations())<min(240,len(self.slots)),'attempt cap'
  assert slot in self.slots,'unknown slot'
  save(self.root/'reservations'/f"{slot['id']}.json",{'utc':utc(),'slot':slot['id'],'request_sha256':request_sha,'mode':self.mode,'status':'RESERVED_BEFORE_SEND'})
 def finish(self,slot,result):save(self.root/'results'/f"{slot['id']}.json",result)
 def summary(self):
  unfinished=self.recover();rr=[read(p) for p in sorted((self.root/'results').glob('*.json'))];reserved=len(self.reservations());counts={}
  for r in rr:counts[r['status']]=counts.get(r['status'],0)+1
  unknown=len(unfinished)+sum(r['status']=='UNKNOWN' for r in rr)
  usages=[r['usage'] for r in rr if isinstance(r.get('usage'),dict) and all(type(r['usage'].get(k)) is int and r['usage'][k]>=0 for k in ['prompt_tokens','completion_tokens'])]
  return {'mode':self.mode,'total_slots':len(self.slots),'reserved':reserved,'complete_http_returns':sum(r.get('complete_http_return',False) for r in rr),'unknown':unknown,'not_started':len(self.slots)-reserved,'counts':counts,'reported_usage_records':len(usages),'usage_unavailable_attempts':reserved-len(usages),'reported_prompt_tokens':sum(u.get('prompt_tokens',0) for u in usages),'reported_completion_tokens':sum(u.get('completion_tokens',0) for u in usages),'stopped':(self.root/'STOP.json').exists(),'currency_cost':'UNKNOWN unless no live reservations; no price invented'}

def size(folder):return sum(f.stat().st_size for f in Path(folder).rglob('*') if f.is_file())
def clean_env():
 env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP'] if k in os.environ}
 root=os.environ.get('SystemRoot',r'C:\Windows');env.update(SystemRoot=root,COMSPEC=str(Path(root)/'System32/cmd.exe'),PATH=str(Path(root)/'System32')+os.pathsep+'D:/iverilog/bin');return env

def bounded_process(argv,folder,label,timeout,env):
 folder=Path(folder);out=folder/(label+'.stdout.bin');err=folder/(label+'.stderr.bin');start=time.monotonic();rc=None;reason=None;launch=None
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
 if max(out.stat().st_size,err.stat().st_size)>2097152 or size(folder)>8388608:reason=reason or 'resource_limit'
 result={'returncode':rc,'limit_reason':reason,'launch_error':launch,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
 save(folder/(label+'-receipt.json'),result);return result

def judge(slot,folder,rtl,process=bounded_process):
 folder=Path(folder);task=slot['task'];save_bytes(folder/'dut.sv',rtl.encode())
 for dest,ext in [('reference.sv','ref.sv'),('testbench.sv','test.sv')]:save_bytes(folder/dest,(BATCH/'originals/dataset_spec-to-rtl'/f'{task}_{ext}').read_bytes())
 env=clean_env();phases=[]
 for name,argv,limit in [('compile',['D:/iverilog/bin/iverilog.exe','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o','sim.vvp','dut.sv','testbench.sv','reference.sv'],15),('simulate',['D:/iverilog/bin/vvp.exe','sim.vvp'],10)]:
  assert sha(Path(argv[0]))==read(BATCH/'calibration-plan.json')['tools'][str(Path(argv[0]))],'tool drift'
  result=process(argv,folder,name,limit,env);phases.append(result)
  if result['launch_error'] or result['limit_reason'] in ['resource_limit','cleanup_unknown']:return {'status':'INFRASTRUCTURE_ERROR','stage':name,'stop':True,'phases':phases}
  if result['returncode']!=0 or result['limit_reason']:return {'status':'COMPILE_ERROR' if name=='compile' else 'SIM_ERROR_OR_TIMEOUT','stage':name,'stop':False,'phases':phases}
 text=(folder/'simulate.stdout.bin').read_bytes().decode('utf-8',errors='replace');matches=[re.fullmatch(r'Mismatches: (\d+) in (\d+) samples',s) for s in text.splitlines()];matches=[(int(m[1]),int(m[2])) for m in matches if m]
 if len(matches)!=1 or matches[0][1]==0 or 'TIMEOUT' in text.upper():return {'status':'SIM_ERROR_OR_TIMEOUT','stage':'simulate','stop':False,'phases':phases,'receipt':matches}
 return {'status':'REFERENCE_PASS' if matches[0][0]==0 else 'REFERENCE_FAIL','stage':'original_test','stop':False,'phases':phases,'receipt':matches,'independent_oracle':False,'additional_sat_event':'NOT_SUPPORTED_PENDING_CONTRACT_REVIEW'}

def process_response(slot,folder,envelope,judge_fn=judge):
 base={'slot':slot['id'],'requested_model':slot['model'],'complete_http_return':envelope.get('outcome')=='HTTP_OK','usage':None}
 def outcome(status,stage,stop,**extras):return dict(base,status=status,stage=stage,stop=stop,**extras)
 if envelope.get('outcome')=='UNKNOWN':return outcome('UNKNOWN','transport',True)
 if envelope.get('outcome')!='HTTP_OK':return outcome('SERVICE_ERROR','transport',True,http_status=envelope.get('http_status'),error=envelope.get('outcome'))
 try:
  body=json.loads(envelope['body']);base['response_model']=body.get('model');base['usage']=body.get('usage');base['response_id']=body.get('id')
  if body.get('model')!=slot['model']:return outcome('MODEL_ID_MISMATCH','transport',True)
  u=body.get('usage');assert isinstance(u,dict) and all(type(u.get(k)) is int and u[k]>=0 for k in ['prompt_tokens','completion_tokens'])
  if u['completion_tokens']>8192:return outcome('BUDGET_VIOLATION','transport',True)
  choices=body['choices'];assert isinstance(choices,list) and len(choices)==1
  c=choices[0];message=c['message'];assert message.get('role')=='assistant' and not message.get('tool_calls') and not message.get('function_call')
  raw=message.get('content');assert isinstance(raw,str) and raw.strip();base['finish_reason']=c.get('finish_reason')
 except (ValueError,KeyError,TypeError,AssertionError):return outcome('SERVICE_PROTOCOL_ERROR','transport',True)
 if len(raw.encode())<=131072:save_bytes(Path(folder)/'model-output.txt',raw.encode())
 if c.get('finish_reason')=='length':return outcome('EXTRACTION_ERROR','extraction',False,reason='token_limit')
 if c.get('finish_reason') not in ['stop']:return outcome('SERVICE_PROTOCOL_ERROR','transport',True,reason='unexpected_finish_reason')
 try:rtl=extract(raw)
 except Exception as e:
  if hasattr(e,'status') and hasattr(e,'stage'):return outcome(e.status,e.stage,False,reason=str(e))
  raise
 verdict=judge_fn(slot,folder,rtl);return dict(base,**verdict)
