"""New explicitly authorized 36, not recovery of old UNKNOWN. Default read-only."""
import argparse,datetime,hashlib,importlib.util,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
sys.path.insert(0,str(P/'reuse'))
import console_bridge_v3 as bridge
import transport
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def save(p,obj):write(p,json.dumps(obj,ensure_ascii=False,indent=2).encode())
def stop(root,reason):
 if not (root/'STOP.json').exists():save(root/'STOP.json',{'reason':reason,'utc':utc()})
def verify():
 lock=read(P/'source-lock.json')
 require(all(sha(P/n)==h for n,h in lock.items()),'New source/input locks changed')
 require(all(sha(R/n)==h for n,h in read(P/'parent-evidence-lock.json').items()),'Parent evidence changed')
 batch=read(P/'batch.json');parent=read(P/'inputs/parent-manifest.json')
 require(sha(P/'inputs/parent-manifest.json')==batch['parent_manifest_sha256'],'Parent manifest mismatch')
 require(all(sha(P/'inputs'/n)==h for n,h in batch['files'].items()),'Frozen inputs changed')
 require(batch['new_max_calls']==36 and batch['cumulative_max_opportunities']==37 and len(batch['slots'])==36,'Budget mismatch')
 require(batch['runtime_root']==str(P/'live'),'Live root changed')
 require([s['ordinal'] for s in batch['slots']]==list(range(1,37)),'Order mismatch')
 require(batch['route']=={'endpoint':bridge.ENDPOINT,'proxy_url':None},'Route changed')
 for a,b in zip(batch['slots'],parent['slots']):
  require(a['id']==f"rag36b1-{a['ordinal']:03d}" and a['parent_slot_id']==b['id'],'ID mapping mismatch')
  require({k:v for k,v in a.items() if k not in ('id','parent_slot_id','request_sha256')}=={k:v for k,v in b.items() if k!='id'},'Original slot metadata changed')
  require(a['request_sha256']==parent['files'][a['request']],'Request binding changed')
  require(not (R/'validation/console-multimodel-20261024-v1/slot-reservations'/f"{b['id']}.json").exists() or a['ordinal']==1,'Old batch advanced; halt for review')
 return batch
def bindings():return {n.replace('.json','_sha256'):sha(P/n) for n in ('source-lock.json','batch.json','parent-evidence-lock.json','offline-audit.json')}
def gate(release_path):
 batch=verify();rel=read(release_path)
 require(rel.get('decision')=='NEW36_SCRIPT_EXECUTION_RELEASE' and rel.get('user_approved') is True,'New coordinator release required')
 require(rel.get('reviewer_thread_id')=='01a12088-049c-7f32-8167-48be03bcc145','Coordinator identity mismatch')
 require(rel.get('bindings')==bindings(),'Release bindings mismatch')
 require(rel.get('permitted_slots')==[s['id'] for s in batch['slots']],'Release slot mismatch')
 require(rel.get('new_max_calls')==36 and rel.get('cumulative_max_opportunities')==37,'Release budget mismatch')
 require(rel.get('old_unknown_preserved') is True and rel.get('manual_start_only') is True,'Parent/manual approval missing')
 require(rel.get('budget_policy')=='calls_only' and rel.get('automatic_retries')==0 and rel.get('request_timeout_seconds')==180,'Policy mismatch')
 require(rel.get('runtime_root')==str(P/'live'),'Release runtime mismatch')
 require(read(P/'offline-audit.json')['passed'] is True,'Offline audit failed')
 return batch

FILES=['request.json','reservation.json','transport-response.json','model-output.txt','dut.sv','testbench.sv','reference.sv','result.json','local/input-lock.json','local/compile.json','local/simulate.json','local/synthesis.json','local/synthesis.ys','local/netlist.json','local/netlist.v','local/wave.vcd','local/sim.vvp','local/dut.sv','local/testbench.sv','local/reference.sv','receipt-write-error.json']
def path_probe(root,slots):
 """Probe exact future file paths, before reservations or POST. Remove only probes."""
 root=Path(root);require(not (root/'RUN_STARTED.json').exists(),'Batch already started: no automatic resume')
 paths=[root/'jobs'/f"{s['ordinal']:03d}"/n for s in slots for n in FILES]
 require(max(len(str(x.resolve())) for x in paths)<240,'Path too long; blocked before send')
 for path in paths:
  require(not path.exists(),'Existing job evidence; no overwrite')
  path.parent.mkdir(parents=True,exist_ok=True)
  payload=b'OFFLINE_PATH_PROBE'
  write(path,payload)
  require(path.read_bytes()==payload,'Path write/read failed')
  path.unlink() # only this newly written probe
 # local_replay requires a fresh local directory, so remove our now-empty probe dirs.
 for s in slots:(root/'jobs'/f"{s['ordinal']:03d}"/'local').rmdir()
 return {'paths_tested':len(paths),'max_path':max(len(str(x.resolve())) for x in paths),'network_requests':0}
def tools_check():
 for f in ('D:/iverilog/bin/iverilog.exe','D:/iverilog/bin/vvp.exe'):require(Path(f).is_file(),'Required Icarus executable absent')
 require(shutil.which('wsl.exe') is not None,'WSL absent')
 env={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP','PATH','USERPROFILE') if k in os.environ}
 p=subprocess.run(['wsl.exe','-d','Ubuntu','--exec','sh','-c','command -v yosys'],capture_output=True,timeout=15,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 require(p.returncode==0 and p.stdout.strip(),'Ubuntu Yosys unavailable')
 return {'icarus_paths_exist':True,'yosys_command_found':True,'network_requests':0,'eda_runs':0}
def reservation_paths(batch,s):
 return [Path(batch['global_reservations'])/f"{s['id']}.json",R/'validation/console-openrouter-20261024-v1/slot-reservations'/f"{s['id']}.json"]
def available(batch):
 for s in batch['slots']:
  require(all(not p.exists() for p in reservation_paths(batch,s)),'Already reserved; no resend')
  for rel in ('exploration/20261024/public-rag-next-executor-v1/runtime/live-run/reservations','exploration/20261023/direct-api-v1/runtime/live-run/reservations'):
   require(not (R/rel/f"{s['id']}.json").exists(),'Historical reservation conflict')

def process_response(s,folder,env,judge):
 result={'status':env.get('outcome','UNKNOWN'),'stop':True,'usage':None,'cost':None,'complete_http_return':env.get('outcome')=='HTTP_OK'}
 require(env.get('request_sha256')==s['request_sha256'],'Receipt payload hash mismatch')
 if env.get('outcome')!='HTTP_OK':return result
 body=json.loads(env['body']);result['usage']=body.get('usage')
 result['cost']=body.get('usage',{}).get('cost') if isinstance(body.get('usage'),dict) else None
 result.update(response_model=body.get('model'),reported_provider=body.get('provider'))
 if body.get('model')!=s['model'] or body.get('provider')!='OpenAI':result['status']='MODEL_OR_PROVIDER_MISMATCH';return result
 choices=body['choices'];require(len(choices)==1 and choices[0].get('finish_reason')=='stop','Incomplete response')
 msg=choices[0]['message'];require(msg.get('role')=='assistant' and not msg.get('tool_calls') and not msg.get('function_call'),'Unexpected assistant format')
 text=msg['content'];require(isinstance(text,str) and len(text.encode())<=131072,'Invalid response size')
 write(folder/'model-output.txt',text.encode())
 try:rtl=bridge.extract(text,s.get('top','TopModule'))
 except Exception as e:result.update(status='EXTRACTION_ERROR',error_type=type(e).__name__);return result
 write(folder/'dut.sv',rtl.encode())
 for k,n in [('reference','reference.sv'),('testbench','testbench.sv')]:write(folder/n,(P/'inputs'/s[k]).read_bytes())
 local=judge(folder,folder/'local',s['expected_checks'],s.get('top','TopModule'),s.get('assets',[]))
 result.update(status='GENERATED_UNVERIFIED',rtl_sha256=sha(folder/'dut.sv'),local=local)
 result['stop']=bool(local.get('infrastructure_stop',True)) or local.get('fixed_test') not in ('FIXED_TEST_PASS','FUNCTION_FAIL','COMPILE_ERROR','CHECK_COUNT_DIFFERENT') or local.get('synthesis') not in ('SYNTH_PASS','SYNTH_FAIL')
 return result

def summary(root,batch):
 root=Path(root);rows=[];reserved=0
 for s in batch['slots']:
  job=root/'jobs'/f"{s['ordinal']:03d}"
  occupied=(job/'reservation.json').exists() or (Path(batch['global_reservations'])/f"{s['id']}.json").exists()
  reserved+=int(occupied)
  try:r=read(job/'result.json') if (job/'result.json').exists() else {'status':'UNKNOWN' if occupied else 'NOT_STARTED','usage':None,'cost':None}
  except (ValueError,OSError):r={'status':'UNKNOWN','usage':None,'cost':None}
  rows.append(dict(r,id=s['id'],ordinal=s['ordinal']))
 costs=[r['cost'] for r in rows if type(r.get('cost')) in (int,float)]
 return {'old_unknown':1,'new_max_calls':36,'cumulative_max_opportunities':37,'new_reserved':reserved,'total_reserved_including_old':1+reserved,'new_not_started':36-reserved,'counts':{k:sum(r['status']==k for r in rows) for k in set(r['status'] for r in rows)},'reported_new_cost_sum':sum(costs) if costs else None,'old_unknown_cost':None,'complete_total_bill_known':False,'stopped':(root/'STOP.json').exists(),'rows':rows}

def execute(batch,root,send,judge,check=lambda:None,probe=path_probe):
 """Private engine; CLI only calls it after an exact new release. Tests inject fake IO."""
 root=Path(root);root.mkdir(parents=True,exist_ok=True);held=False
 try:
  save(root/'exclusive.lock',{'pid':os.getpid(),'utc':utc()});held=True
  require(not (root/'RUN_STARTED.json').exists() and not (root/'STOP.json').exists(),'Run already started or stopped; no automatic resume')
  check();available(batch)
  proof=probe(root,batch['slots']);save(root/('path-preflight-'+uuid.uuid4().hex+'.json'),proof)
  save(root/'RUN_STARTED.json',{'utc':utc(),'batch_sha256':sha(P/'batch.json'),'ids':[s['id'] for s in batch['slots']]})
  for s in batch['slots']:
   check()
   require(all(not p.exists() for p in reservation_paths(batch,s)),'Cross-entry reservation conflict')
   folder=root/'jobs'/f"{s['ordinal']:03d}";folder.mkdir(parents=True,exist_ok=True)
   raw=(P/'inputs'/s['request']).read_bytes();require(hashlib.sha256(raw).hexdigest()==s['request_sha256'],'Request bytes drift')
   write(folder/'request.json',raw)
   # Open durable response destination BEFORE irreversible reservation / any send.
   with (folder/'transport-response.json').open('xb') as receipt:
    reservation={'id':s['id'],'parent_slot_id':s['parent_slot_id'],'request_sha256':s['request_sha256'],'batch_sha256':sha(P/'batch.json'),'status':'RESERVED_BEFORE_SEND','utc':utc()}
    save(Path(batch['global_reservations'])/f"{s['id']}.json",reservation)
    save(folder/'reservation.json',reservation)
    result={'status':'UNKNOWN','stop':True,'usage':None,'cost':None};env=None
    try:
     env=send(raw,batch['route'],180)
     receipt.write(json.dumps(env,ensure_ascii=False).encode());receipt.flush();os.fsync(receipt.fileno())
     result=process_response(s,folder,env,judge)
    except BaseException as e:
     result.update(status='UNKNOWN' if env is None else 'POSTPROCESSING_ERROR',stop=True,error_type=type(e).__name__)
     if env is not None:
      # Preserve an in-memory receipt if the primary response write failed.
      try:
       if not (folder/'receipt-write-error.json').exists():save(folder/'receipt-write-error.json',env)
      except BaseException:pass
    result.update(id=s['id'],parent_slot_id=s['parent_slot_id'],request_sha256=s['request_sha256'],utc=utc())
    save(folder/'result.json',result)
   print(json.dumps({'ordinal':s['ordinal'],'id':s['id'],'status':result['status'],'stop':result['stop']},ensure_ascii=False),flush=True)
   if result['stop']:stop(root,result['status']);break
  out=summary(root,batch);save(root/('summary-'+uuid.uuid4().hex+'.json'),out);return out
 except BaseException:
  if held:stop(root,'INFRASTRUCTURE_OR_INTERRUPTION_NO_AUTO_RESUME')
  raise
 finally:
  if held:(root/'exclusive.lock').unlink()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['status','preflight','run']);ap.add_argument('--release');args=ap.parse_args()
 if args.action=='status':print(json.dumps(summary(P/'live',read(P/'batch.json')),ensure_ascii=False,indent=2));return 0
 batch=gate(args.release);root=Path(batch['runtime_root'])
 available(batch);require(not (root/'RUN_STARTED.json').exists() and not (root/'STOP.json').exists(),'Run already started/stopped')
 proof=tools_check()
 if args.action=='preflight':
  print(json.dumps({'ready':True,'tools':proof,'paths':path_probe(root,batch['slots']),'new_max_calls':36,'cumulative_max_opportunities':37,'network_requests':0}));return 0
 secret=os.environ.get('OPENROUTER_API_KEY','');require(bool(secret),'Hidden credential required')
 def live_send(raw,route,timeout):
  env=transport.send_once(raw,route,secret,timeout)
  require(secret not in json.dumps(env,ensure_ascii=False),'Secret echo rejected')
  return env
 out=execute(batch,root,live_send,bridge.local_replay,check=lambda:gate(args.release))
 print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False));return 1 if out['stopped'] else 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:print('STOP: '+type(e).__name__+'; preserve evidence; no retry.');raise SystemExit(2)
