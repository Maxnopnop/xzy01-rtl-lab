"""Coordinator's one-time exact96 technical release. Preflight only; never generates."""
import json,hashlib,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
EXE=OUT.parents[1]/'exploration/20261024/public-rag-next-executor-v1'
B=EXE.parent/'public-rag-next-v1'
def read(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
audit=read(OUT/'audit.json');assert audit['status']=='OFFLINE_TECHNICAL_CHECKS_PASS'
for p,h in read(OUT/'evidence-lock.json').items():assert sha(Path(p))==h,p
for p in ('powershell-tests.json','powershell51-tests.json'):
    assert all(r['passed'] for r in read(EXE/p))
assert not (EXE/'runtime/live-run').exists(),'Unexpected production ledger'
release={
    'decision':'TECHNICAL_RELEASE',
    'utc':datetime.now(timezone.utc).isoformat(),
    'reviewer_thread_id':'01a12088-049c-7f32-8167-48be03bcc145',
    'source_lock_sha256':sha(EXE/'source-lock.json'),
    'input_lock_sha256':sha(EXE/'input-lock.json'),
    'route_sha256':sha(EXE/'route.json'),
    'input_packet_sha256':sha(B/'packet-lock.json'),
    'max_attempts':96,'permitted_ordinals':list(range(1,97)),
    'calibration_summary_sha256':sha(EXE/'calibration/summary.json'),
    'mock_summary_sha256':sha(EXE/'mock/summary.json'),
    'automatic_retries':0,'batch_wall_seconds':None,'request_timeout_seconds':180,
    'user_approved_8_tasks':True,'user_authorization':'用这些题开始吧',
    'conditional_reference_limitations_accepted':True,
    'models':['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol'],
    'concurrency':1,'max_completion_tokens':None,'allow_fallbacks':False,
    'coordinator_audit_sha256':sha(OUT/'audit.json'),
    'source_and_original_evidence_unchanged':True,
    'no_repeat_of_old240':True,
    'independent_oracle_established':False,
}
runtime=EXE/'runtime';runtime.mkdir(exist_ok=True)
with (runtime/'technical-release.json').open('x',encoding='utf-8') as f:json.dump(release,f,ensure_ascii=False,indent=2)
# Synthetic credential is child-only. This inspected command only checks local hashes and gates.
env=os.environ.copy();env['OPENROUTER_API_KEY']='OFFLINE_SYNTHETIC_PREFLIGHT_ONLY'
proc=subprocess.run([sys.executable,'-B',str(EXE/'runner.py'),'preflight'],env=env,capture_output=True,timeout=30)
report=json.loads(proc.stdout)
assert proc.returncode==0 and report['ready'] and report['network_requests']==0
assert not (runtime/'live-run').exists()
(OUT/'released-preflight.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
    'release_sha256':sha(runtime/'technical-release.json'),'preflight':report,'credential':'SYNTHETIC_CHILD_ONLY',
    'generation_calls':0,'production_ledger_exists':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'technical_release':True,'local_preflight_pass':True,'generation_calls':0,'requires_user_terminal_key':True}))
