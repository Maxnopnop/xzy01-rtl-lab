"""OpenRouter client adaptation. Preflight is local; run requires coordinator release."""
import argparse,json,os,sys,time,uuid
from pathlib import Path
import core,transport

HERE=Path(__file__).resolve().parent
REV=HERE.parent/'cli-cache-repair-v1'
RUNTIME=HERE/'runtime'
LIVE=RUNTIME/'live-run'
MODELS=core.MODELS
WIRE={m:'openai/'+m for m in MODELS}

def route_check(route,local_mock=False):
    resolved=transport.route_values(route,os.environ,local_mock)
    if not local_mock:
        assert route['endpoint']=='https://openrouter.ai/api/v1/chat/completions','OpenRouter endpoint must match reviewed route'
        assert route['api_key_env']=='OPENROUTER_API_KEY','Unexpected credential variable'
    assert isinstance(route['provider_only'],list) and len(route['provider_only'])==1 and isinstance(route['provider_only'][0],str) and route['provider_only'][0],'One reviewed provider slug required'
    assert isinstance(route['expected_provider'],str) and route['expected_provider'],'Reviewed response provider name required'
    return resolved

def prepare_slots(route):
    manifest=core.read(REV/'revised-request-manifest.json');original=core.read(core.BATCH/'slots.json')
    assert len(manifest)==len(original)==240
    result=[]
    for old,new in zip(original,manifest):
        assert old['id']==new['slot_id'] and old['ordinal']==new['ordinal']
        src=REV/'revised-requests'/f"{old['id']}.json";raw=src.read_bytes()
        assert core.digest(raw)==new['new_sha256'],'Revised request drift'
        obj=json.loads(raw);assert set(obj)=={'model','messages','stream'} and obj['model']==old['model'] and obj['stream'] is False
        assert obj['messages']==core.read(core.BATCH/'messages'/f"{old['task']}__{old['condition']}.json")
        obj['model']=WIRE[old['model']]
        obj['provider']={'only':route['provider_only'],'allow_fallbacks':False,'require_parameters':True}
        wire=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        result.append(dict(old,source_request_sha256=new['new_sha256'],request_sha256=core.digest(wire),wire_model=obj['model'],expected_provider=route['expected_provider'],wire_bytes=wire))
    return result

def validate_payload(slot,raw):
    assert core.digest(raw)==slot['request_sha256'],'Wire bytes drift'
    obj=json.loads(raw)
    assert set(obj)=={'model','messages','stream','provider'}
    assert obj['model']==WIRE[slot['model']] and obj['stream'] is False
    assert obj['messages']==core.read(core.BATCH/'messages'/f"{slot['task']}__{slot['condition']}.json"),'Message drift'
    assert obj['provider']['allow_fallbacks'] is False and obj['provider']['require_parameters'] is True
    return obj

def preflight(route_file,release_file):
    report={'ready':False,'network_requests':0,'inference_access':'UNVERIFIED_UNTIL_FORMAL_RETURN','errors':[],'credential_present':False}
    try:
        locks=core.read(HERE/'source-lock.json');assert all(core.sha(HERE/k)==v for k,v in locks.items()),'Source drift'
        inputs=core.read(HERE/'input-lock.json');assert all(core.sha(Path(k))==v for k,v in inputs.items()),'Input binding drift'
        route=core.read(route_file);route_check(route)
        report['credential_present']=bool(os.environ.get(route['api_key_env']))
        assert report['credential_present'],'Credential absent in this process'
        prepare_slots(route)
        release=core.read(release_file)
        assert release['decision']=='TECHNICAL_RELEASE' and release['reviewer_thread_id']=='01a12088-049c-7f32-8167-48be03bcc145','Coordinator release required'
        assert release['source_lock_sha256']==core.sha(HERE/'source-lock.json') and release['input_lock_sha256']==core.sha(HERE/'input-lock.json') and release['route_sha256']==core.sha(route_file),'Release bindings mismatch'
        assert release['models']==MODELS and release['wire_models']==list(WIRE.values()) and release['max_attempts']==240
        assert release['allow_fallbacks'] is False and release['automatic_retries']==0
        for flag in ['client_payload_audited','client_no_retry_audited','upstream_catalog_reviewed','service_boundary_acknowledged']:
            assert release.get(flag) is True,flag+' not reviewed'
        assert isinstance(release['metadata_evidence'],list) and release['metadata_evidence']
        for e in release['metadata_evidence']:assert core.sha(e['path'])==e['sha256'],'Metadata evidence drift'
        permitted=release['permitted_ordinals']
        assert permitted==list(range(1,len(permitted)+1)) and 1<=len(permitted)<=240,'Authorization must be an original prefix'
        report.update(ready=True,permitted_ordinals=permitted,route_proxy_explicit=True)
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as e:
        report['errors'].append(str(e) if isinstance(e,AssertionError) else type(e).__name__)
    return report

def live_transport(slot,folder,timeout,route_file,local_mock=False):
    route=core.read(route_file);resolved=route_check(route,local_mock)
    env=core.clean_env()
    # Explicit proxy crosses worker boundary in route.json; ambient proxies are not consulted.
    env['RTL_RAG_SECRET']='OFFLINE_SYNTHETIC_TOKEN_ONLY' if local_mock else os.environ[route['api_key_env']]
    core.save(folder/'route.json',resolved)
    target=folder/'transport-response.json'
    phase=core.bounded_process([sys.executable,'-B',str(HERE/'transport.py'),str(folder/'request.json'),str(folder/'route.json'),str(target),str(timeout)],folder,'http',timeout+.5,env)
    if target.exists():
        try:
            result=core.read(target)
            if phase['returncode']!=0 or phase['limit_reason']:result['forced_stop']='WORKER_FAILURE_AFTER_RECEIPT'
            return result
        except (OSError,ValueError):pass
    return {'outcome':'UNKNOWN','request_sha256':slot['request_sha256']}

def execute(root,slots,mode,transport_fn,judge_fn=core.judge,gate=None,permitted=None):
    ledger=core.Ledger(root,slots,mode);ledger.lock()
    try:
        if ledger.recover() or (ledger.root/'STOP.json').exists():return ledger.summary()
        start=core.read(ledger.root/'identity.json')['start_epoch']
        for slot in slots:
            if (ledger.root/'results'/f"{slot['id']}.json").exists():continue
            if permitted is not None and slot['ordinal'] not in permitted:break
            elapsed=time.time()-start
            if elapsed<0 or elapsed>=12000 or core.size(root)>524288000:
                ledger.stop('WALL_OR_STORAGE_LIMIT');break
            if gate and not gate()['ready']:
                ledger.stop('TECHNICAL_GATE_CHANGED');break
            raw=slot['wire_bytes'];validate_payload(slot,raw)
            folder=ledger.root/'jobs'/f"{slot['ordinal']:03d}";folder.mkdir(parents=True)
            core.save_bytes(folder/'request.json',raw)
            ledger.reserve(slot,core.digest(raw))
            envelope=None
            try:
                envelope=transport_fn(slot,folder,min(180,12000-elapsed))
                if not (folder/'transport-response.json').exists():core.save(folder/'transport-response.json',envelope)
                if envelope.get('request_sha256')!=slot['request_sha256']:
                    result={'slot':slot['id'],'status':'PAYLOAD_MISMATCH','stage':'transport','stop':True,'complete_http_return':False}
                else:result=core.process_response(slot,folder,envelope,judge_fn)
            except BaseException as exc:
                result={'slot':slot['id'],'status':'UNKNOWN' if not envelope or envelope.get('outcome')!='HTTP_OK' else 'POSTPROCESSING_ERROR','stage':'transport_or_processing','stop':True,'complete_http_return':bool(envelope and envelope.get('outcome')=='HTTP_OK'),'error_type':type(exc).__name__}
            result.update(mode=mode,utc=core.utc(),request_sha256=slot['request_sha256'],source_request_sha256=slot['source_request_sha256'])
            label=next(x for x in core.read(core.BATCH/'task-labels.json') if x['id']==slot['task'])
            result.update(task_label=label['current_label'],clear_subset=label['clear_subset'],not_a_spec_violation_claim=True)
            ledger.finish(slot,result)
            if result.get('stop'):ledger.stop(result['status'])
            if result.get('stop'):break
        return ledger.summary()
    except BaseException:
        ledger.stop('UNEXPECTED_INFRASTRUCTURE_FAILURE_NO_AUTO_RESUME');raise
    finally:ledger.unlock()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['preflight','run']);ap.add_argument('--route',type=Path,default=RUNTIME/'route.local.json');args=ap.parse_args()
    release=RUNTIME/'technical-release.json';report=preflight(args.route,release)
    if args.command=='preflight' or not report['ready']:
        print(json.dumps(report,ensure_ascii=False));return 0 if report['ready'] else 2
    slots=prepare_slots(core.read(args.route))
    result=execute(LIVE,slots,'LIVE',lambda s,f,t:live_transport(s,f,t,args.route),gate=lambda:preflight(args.route,release),permitted=report['permitted_ordinals'])
    core.save(LIVE/('summary-'+uuid.uuid4().hex+'.json'),result);print(json.dumps(result));return 1 if result['stopped'] else 0

if __name__=='__main__':raise SystemExit(main())
