"""Frozen bytes -> single request -> original TB. New96 ledger, no batch wall cap."""
import argparse,json,os,sys,uuid
from pathlib import Path
import core,transport
from ledger import Ledger
HERE=Path(__file__).resolve().parent;BATCH=core.BATCH
RUNTIME=HERE/'runtime';LIVE=RUNTIME/'live-run'
MAX_DISK=536870912;MAX_JOB=8388608
def binding():return {'source_lock_sha256':core.sha(HERE/'source-lock.json'),'input_lock_sha256':core.sha(HERE/'input-lock.json'),'route_sha256':core.sha(HERE/'route.json')}
def verify_inputs():
    assert core.sha(BATCH/'packet-lock.json')==core.BATCH_SHA,'Input packet changed'
    assert all(core.sha(Path(p))==h for p,h in core.read(HERE/'input-lock.json').items()),'Input/tool drift'
    slots=core.read(BATCH/'C/slots.json');assert len(slots)==96
    for n,s in enumerate(slots,1):
        assert s['ordinal']==n and s['status']=='NOT_STARTED' and not s['reserved']
        validate(s,(BATCH/s['request']).read_bytes())
    return slots
def validate(s,raw):
    assert core.digest(raw)==s['request_sha256'],'Frozen request bytes drift'
    obj=json.loads(raw);assert set(obj)=={'model','messages','stream','provider'}
    assert s['model'] in core.MODELS and obj['model']==s['wire_model']=='openai/'+s['model'] and obj['stream'] is False
    assert obj['messages']==core.read(BATCH/'C/messages'/f"{s['task']}__{s['condition']}.json"),'Message drift'
    assert obj['provider']=={'only':['openai'],'allow_fallbacks':False,'require_parameters':True}
    return obj
def preflight():
    r={'ready':False,'network_requests':0,'credential_present':bool(os.environ.get('OPENROUTER_API_KEY')),'errors':[]}
    try:
        assert all(core.sha(HERE/p)==h for p,h in core.read(HERE/'source-lock.json').items()),'Source drift'
        verify_inputs();route=core.read(HERE/'route.json');transport.route_values(route,os.environ)
        assert route==core.read(BATCH/'protocol/route.json'),'Route changed'
        cal=core.read(HERE/'calibration/summary.json');assert cal['passed'] and cal['compile_attempts']==cal['sim_attempts']==8,'Calibration blocked'
        assert core.read(HERE/'mock/summary.json')['passed'],'Mock audit blocked'
        release=core.read(RUNTIME/'technical-release.json')
        assert release['decision']=='TECHNICAL_RELEASE' and release['reviewer_thread_id']=='01a12088-049c-7f32-8167-48be03bcc145','Coordinator release required'
        assert all(release[k]==v for k,v in binding().items()),'Release bindings mismatch'
        assert release['input_packet_sha256']==core.BATCH_SHA and release['max_attempts']==96 and release['permitted_ordinals']==list(range(1,97)),'Exact96 release required'
        assert release['calibration_summary_sha256']==core.sha(HERE/'calibration/summary.json') and release['mock_summary_sha256']==core.sha(HERE/'mock/summary.json'),'Audit bindings mismatch'
        assert release['automatic_retries']==0 and release['batch_wall_seconds'] is None and release['request_timeout_seconds']==180
        assert release['user_approved_8_tasks'] is True and release['conditional_reference_limitations_accepted'] is True
        assert r['credential_present'],'Credential absent in user process'
        r.update(ready=True,permitted_ordinals=release['permitted_ordinals'],max_attempts=96)
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as e:r['errors'].append(str(e) if isinstance(e,AssertionError) else type(e).__name__)
    return r
def send(slot,folder,timeout,route=None,local_mock=False):
    cfg=core.read(HERE/'route.json') if route is None else route
    if not local_mock:assert cfg==core.read(BATCH/'protocol/route.json')
    resolved=transport.route_values(cfg,{},local_mock)
    env=core.clean_env();env['RTL_RAG_SECRET']='OFFLINE_SYNTHETIC_TOKEN_ONLY' if local_mock else os.environ['OPENROUTER_API_KEY']
    core.save(folder/'route.json',resolved);target=folder/'transport-response.json'
    phase=core.bounded_process([sys.executable,'-B',str(HERE/'transport.py'),str(folder/'request.json'),str(folder/'route.json'),str(target),str(timeout)],folder,'http',timeout+.5,env)
    if target.exists():
        try:
            result=core.read(target)
            if phase['returncode']!=0 or phase['limit_reason']:result['forced_stop']='WORKER_FAILURE_AFTER_RECEIPT'
            return result
        except (OSError,ValueError):pass
    return {'outcome':'UNKNOWN','request_sha256':slot['request_sha256']}
def execute(root,slots,mode,send_fn,judge_fn=core.judge,gate=None,run_binding=None):
    ledger=Ledger(root,slots,mode,run_binding or binding())
    try:
        ledger.lock()
        if ledger.recover() or (ledger.root/'STOP.json').exists():return ledger.summary()
        for s in slots:
            if (ledger.root/'results'/f"{s['id']}.json").exists():continue
            if core.size(root)>MAX_DISK-MAX_JOB:ledger.stop('TOTAL_DISK_LIMIT');break
            if gate and not gate()['ready']:ledger.stop('TECHNICAL_GATE_CHANGED');break
            raw=(BATCH/s['request']).read_bytes();validate(s,raw)
            folder=ledger.root/'jobs'/f"{s['ordinal']:03d}";folder.mkdir(parents=True,exist_ok=False)
            core.save_bytes(folder/'request.json',raw);ledger.reserve(s,core.digest(raw))
            envelope=None
            try:
                envelope=send_fn(s,folder,180)
                if not (folder/'transport-response.json').exists():core.save(folder/'transport-response.json',envelope)
                if envelope.get('request_sha256')!=s['request_sha256']:result={'status':'PAYLOAD_MISMATCH','stage':'transport','stop':True,'complete_http_return':False}
                else:result=core.process_response(s,folder,envelope,judge_fn)
                if core.size(folder)>MAX_JOB or core.size(root)>MAX_DISK:result.update(status='RESOURCE_LIMIT',stage='storage',stop=True)
            except BaseException as e:
                result={'status':'UNKNOWN' if not envelope or envelope.get('outcome')=='UNKNOWN' else 'POSTPROCESSING_ERROR','stage':'transport_or_processing','stop':True,'complete_http_return':bool(envelope and envelope.get('outcome')=='HTTP_OK'),'error_type':type(e).__name__}
            row=next(r for r in core.read(BATCH/'B/selection.json')['rows'] if r['id']==s['task'])
            result.update(task=s['task'],condition=s['condition'],sample=s['sample'],task_label=row['status'],history_relation=row['history_review_zh'],independent_oracle=False)
            ledger.finish(s,result)
            if result.get('stop'):ledger.stop(result['status']);break
        return ledger.summary()
    except BaseException:
        if ledger.held:ledger.stop('INFRASTRUCTURE_FAILURE_NO_AUTO_RESUME')
        raise
    finally:ledger.unlock()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['preflight','run']);args=ap.parse_args();report=preflight()
    if args.command=='preflight' or not report['ready']:print(json.dumps(report));return 0 if report['ready'] else 2
    slots=verify_inputs();result=execute(LIVE,slots,'LIVE',send,gate=preflight)
    core.save(LIVE/('summary-'+uuid.uuid4().hex+'.json'),result);print(json.dumps(result));return 1 if result['stopped'] else 0
if __name__=='__main__':raise SystemExit(main())
