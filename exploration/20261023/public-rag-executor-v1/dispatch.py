"""One finite240-slot run. --preflight is read-only to provider; --run needs technical release."""
import argparse,json,os,re,sys,time,uuid
from pathlib import Path
from urllib.parse import urlsplit
import core
HERE=Path(__file__).resolve().parent;RUNTIME=HERE/'runtime';LIVE=RUNTIME/'live-run'

def validate_payload(slot,raw):
 assert core.digest(raw)==slot['request_sha256'],'request bytes drift'
 request=json.loads(raw);assert request['model']==slot['model'] and slot['model'] in core.MODELS
 assert set(request)=={'model','messages','stream','max_completion_tokens'} and request['stream'] is False and type(request['max_completion_tokens']) is int and request['max_completion_tokens']==8192
 assert request['messages']==core.read(core.BATCH/'messages'/f"{slot['task']}__{slot['condition']}.json"),'messages drift'
 return request

def check_release(route_file,release_file):
 errors=[]
 try:
  locks=core.read(HERE/'executor-source-lock.json');assert all(core.sha(HERE/k)==v for k,v in locks.items()),'executor drift'
  core.verify_batch()
  route=core.read(route_file);assert set(route)=={'endpoint','api_key_env'},'unexpected route fields'
  u=urlsplit(route['endpoint']);assert u.scheme=='https' and u.hostname and not(u.username or u.password or u.query or u.fragment) and u.path.endswith('/chat/completions'),'HTTPS chat completions endpoint required'
  assert re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',route['api_key_env']),'invalid credential variable'
  assert os.environ.get(route['api_key_env']),'configured API credential missing'
  release=core.read(release_file)
  assert release['decision']=='TECHNICAL_RELEASE' and release['reviewer_thread_id']=='01a12088-049c-7f32-8167-48be03bcc145','coordinator release required'
  assert release['batch_sha256']==core.BATCH_SHA and release['executor_source_lock_sha256']==core.sha(HERE/'executor-source-lock.json') and release['route_config_sha256']==core.sha(route_file),'release bindings mismatch'
  assert release['models']==core.MODELS and release['max_attempts']==240 and release['max_completion_tokens']==8192,'release budget/model mismatch'
  for key in ['model_access_verified','hard_cap_verified','wrapper_boundary_reviewed','common_parameter_semantics_reviewed']:assert release.get(key) is True,key+' not verified'
  assert isinstance(release.get('evidence'),list) and release['evidence'],'release evidence required'
 except (OSError,ValueError,KeyError,TypeError,AssertionError) as e:errors.append(str(e) if isinstance(e,AssertionError) else type(e).__name__)
 return {'utc':core.utc(),'ready':not errors,'errors':errors,'model_calls':0}

def live_transport(slot,folder,timeout,route_file):
 route=core.read(route_file);env=core.clean_env();env['RTL_RAG_SECRET']=os.environ[route['api_key_env']]
 resultfile=folder/'transport-response.json';core.save(folder/'route.json',{'endpoint':route['endpoint']})
 phase=core.bounded_process([sys.executable,'-B',str(HERE/'http_once.py'),str(folder/'request.json'),str(folder/'route.json'),str(resultfile),str(timeout)],folder,'http',timeout,env)
 if phase['returncode']!=0 or phase['limit_reason'] or phase['launch_error'] or not resultfile.exists():return {'outcome':'UNKNOWN'}
 try:return core.read(resultfile)
 except (ValueError,OSError):return {'outcome':'UNKNOWN'}

def execute(root,slots,mode,transport,judge_fn=core.judge,request_loader=None,gate=None):
 ledger=core.Ledger(root,slots,mode);ledger.lock()
 try:
  if ledger.recover() or (ledger.root/'STOP.json').exists():return ledger.summary()
  start=core.read(ledger.root/'identity.json')['start_epoch']
  for slot in slots:
   if (ledger.root/'results'/f"{slot['id']}.json").exists():continue
   elapsed=time.time()-start
   if elapsed<0 or elapsed>=12000 or core.size(ledger.root)>524288000:ledger.stop('WALL_OR_STORAGE_LIMIT');break
   if gate:
    check=gate()
    if not check['ready']:ledger.stop('TECHNICAL_GATE_CHANGED');break
   raw=request_loader(slot) if request_loader else (core.BATCH/slot['request']).read_bytes();validate_payload(slot,raw)
   folder=ledger.root/'jobs'/f"{slot['ordinal']:03d}";folder.mkdir(parents=True) # never overwrite prior attempt
   core.save_bytes(folder/'request.json',raw)
   # Durable reservation is committed BEFORE the transport callback is invoked.
   ledger.reserve(slot,core.digest(raw))
   env=None
   try:
    env=transport(slot,folder,min(180,12000-elapsed))
    if env.get('outcome')=='UNKNOWN' and (folder/'transport-response.json').exists():
     stored=core.read(folder/'transport-response.json')
     if stored.get('outcome')=='HTTP_OK':env=dict(stored,forced_stop='WORKER_FAILURE_AFTER_DURABLE_RESPONSE')
    if env.get('request_sha256') not in (None,slot['request_sha256']) or (mode=='LIVE' and env.get('outcome')=='HTTP_OK' and not env.get('request_sha256')):result={'slot':slot['id'],'status':'PAYLOAD_MISMATCH','stage':'transport','stop':True,'complete_http_return':False}
    else:
     if not (folder/'transport-response.json').exists():core.save(folder/'transport-response.json',env)
     result=core.process_response(slot,folder,env,judge_fn)
   except BaseException as e:
    # After reservation any interruption is conservatively unknown; never resend.
    complete=isinstance(env,dict) and env.get('outcome')=='HTTP_OK'
    usage=None
    if complete:
     try:usage=json.loads(env['body']).get('usage')
     except (ValueError,TypeError,AttributeError):pass
    result={'slot':slot['id'],'status':'POSTPROCESSING_ERROR' if complete else 'UNKNOWN','stage':'postprocessing' if complete else 'transport','stop':True,'complete_http_return':complete,'usage':usage,'error_type':type(e).__name__}
   result['mode']=mode;result['utc']=core.utc();result['request_sha256']=slot['request_sha256']
   label=next(r for r in core.read(core.BATCH/'task-labels.json') if r['id']==slot['task']);result['task_label']=label['current_label'];result['clear_subset']=label['clear_subset'];result['not_a_spec_violation_claim']=True
   ledger.finish(slot,result)
   if result.get('stop'):ledger.stop(result['status'])
   core.save(ledger.root/'summaries'/f'{len(ledger.reservations()):03d}.json',ledger.summary())
   if result.get('stop'):break
  return ledger.summary()
 except BaseException:
  ledger.stop('UNEXPECTED_INFRASTRUCTURE_FAILURE_NO_AUTOMATIC_RESUME');raise
 finally:ledger.unlock()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['preflight','run']);args=ap.parse_args()
 route=RUNTIME/'route.local.json';release=RUNTIME/'technical-release.json';report=check_release(route,release)
 RUNTIME.mkdir(exist_ok=True);core.save(RUNTIME/('preflight-'+uuid.uuid4().hex+'.json'),report)
 if args.command=='preflight' or not report['ready']:print(json.dumps(report));return 0 if report['ready'] else 2
 slots=core.verify_batch()
 # Fixed live directory; opening another directory cannot reset240attempt accounting.
 summary=execute(LIVE,slots,'LIVE',lambda s,f,t:live_transport(s,f,t,route),gate=lambda:check_release(route,release))
 core.save(LIVE/('final-summary-'+uuid.uuid4().hex+'.json'),summary);print(json.dumps(summary));return 1 if summary['stopped'] else 0
if __name__=='__main__':raise SystemExit(main())
