"""Synthetic-release/identity gate checks, no send or HDL execution."""
import os,json,copy
from pathlib import Path
from unittest.mock import patch
import core,runner,ledger
P=Path(__file__).resolve().parent
root=P/'gate-tests';root.mkdir(exist_ok=False);checks={};slots=runner.verify_inputs()
release=dict(runner.binding(),decision='TECHNICAL_RELEASE',reviewer_thread_id='01a12088-049c-7f32-8167-48be03bcc145',input_packet_sha256=core.BATCH_SHA,max_attempts=96,permitted_ordinals=list(range(1,97)),calibration_summary_sha256=core.sha(P/'calibration/summary.json'),mock_summary_sha256=core.sha(P/'mock/summary.json'),automatic_retries=0,batch_wall_seconds=None,request_timeout_seconds=180,user_approved_8_tasks=True,conditional_reference_limitations_accepted=True)
# Only redirect release lookup to an explicitly synthetic fixture directory. Never create runtime release.
fixture=root/'synthetic-release';fixture.mkdir();path=fixture/'technical-release.json'
with patch.object(runner,'RUNTIME',fixture),patch.dict(os.environ,{'OPENROUTER_API_KEY':'OFFLINE_SYNTHETIC_TOKEN_ONLY'}):
    checks['missing_release_blocks']=not runner.preflight()['ready']
    path.write_text(json.dumps(release));checks['bound_fixture_preflight']=runner.preflight()['ready']
    with patch.dict(os.environ,{'OPENROUTER_API_KEY':''}):checks['empty_key_blocks']=not runner.preflight()['ready']
    for key,value in [('max_attempts',240),('permitted_ordinals',[1,2,3]),('source_lock_sha256','bad'),('input_lock_sha256','bad'),('route_sha256','bad'),('automatic_retries',1)]:
        path.write_text(json.dumps(dict(release,**{key:value})));checks[key+'_drift_blocks']=not runner.preflight()['ready']
    path.write_text(json.dumps(release))
    original_sha=core.sha
    with patch.object(core,'sha',side_effect=lambda p:'bad' if Path(p)==runner.BATCH/'packet-lock.json' else original_sha(p)):
        checks['packet_hash_drift_blocks']=not runner.preflight()['ready']
bind={'fixture':'identity'};ll=ledger.Ledger(root/'identity',slots[:2],'MOCK',bind);ll.lock();ll.unlock()
changed=ledger.Ledger(root/'identity',slots[:2],'MOCK',{'fixture':'changed'})
try:
    changed.lock();checks['identity_drift_blocks']=False
except AssertionError:checks['identity_drift_blocks']=True
finally:changed.unlock()
ll=ledger.Ledger(root/'completed_response_crash',slots[:2],'MOCK',bind);ll.lock();ll.reserve(slots[0],slots[0]['request_sha256']);ll.unlock()
core.save(root/'completed_response_crash/jobs/001/transport-response.json',{'outcome':'HTTP_OK','request_sha256':slots[0]['request_sha256'],'body':json.dumps({'usage':{'prompt_tokens':1,'completion_tokens':2}})})
calls=[];summary=runner.execute(root/'completed_response_crash',slots[:2],'MOCK',lambda *x:calls.append(1),run_binding=bind)
checks['saved_response_no_reprocess_no_resend']=not calls and summary['reserved']==1 and summary['stopped'] and summary['complete_http_returns']==1 and summary['counts']=={'RECOVERY_RESPONSE_UNPROCESSED':1}
core.save(root/'summary.json',{'passed':all(checks.values()),'checks':checks,'generation_requests':0,'eda_calls':0,'synthetic_only':True});print(json.dumps(checks));raise SystemExit(0 if all(checks.values()) else 1)
