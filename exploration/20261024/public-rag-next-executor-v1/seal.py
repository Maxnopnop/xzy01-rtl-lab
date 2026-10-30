import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent/'public-rag-next-v1'
def read(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):
    p=P/n;assert not p.exists(),n;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(P/'source-lock.json')=='fc24d8895d897ee9ace9facb398d991c8110e47ed4cd6b6a4bcd50dd1d14f78c'
assert all(sha(P/n)==h for n,h in read(P/'source-lock.json').items())
assert all(sha(n)==h for n,h in read(P/'input-lock.json').items())
assert all(sha(n)==h for n,h in read(P/'tools-lock.json').items())
assert all(sha(P/'calibration'/n)==h for n,h in read(P/'calibration/evidence-lock.json').items())
assert read(P/'mock/summary.json')['passed'] and read(P/'gate-tests/summary.json')['passed']
bindings={'source_lock_sha256':sha(P/'source-lock.json'),'input_lock_sha256':sha(P/'input-lock.json'),'route_sha256':sha(P/'route.json'),'input_packet_sha256':sha(B/'packet-lock.json'),'calibration_summary_sha256':sha(P/'calibration/summary.json'),'mock_summary_sha256':sha(P/'mock/summary.json')}
put('review-bindings.json',dict(bindings,status='PREPARED_NOT_RELEASED',gate_summary_sha256=sha(P/'gate-tests/summary.json'),calibration_previous_source_lock_sha256=sha(P/'development/calibration-source-lock.json'),release_destination=str(P/'runtime/technical-release.json')))
put('technical-release.example.json',dict(bindings,decision='NOT_RELEASED',reviewer_thread_id='01a12088-049c-7f32-8167-48be03bcc145',max_attempts=96,permitted_ordinals=list(range(1,97)),automatic_retries=0,batch_wall_seconds=None,request_timeout_seconds=180,user_approved_8_tasks=True,conditional_reference_limitations_accepted=False,notice='Template only; coordinator independent review required'))
old=P.parents[1]/'20261023/direct-api-v1';oldlock=read(old/'packet-lock.json');assert all(sha(old/n)==h for n,h in oldlock.items())
legacy=P.parents[1]/'20261023/openrouter-launch-v1/default-regression.txt'
put('preservation.json',{'old_direct_api_packet_entries':len(oldlock),'old_direct_api_mismatches':0,'new_input_packet_entries':len(read(B/'packet-lock.json')),'new_input_mismatches':0,'legacy_regression_log_sha256':sha(legacy),'legacy_regression_log_unchanged_by_this_task':True,'source_files':8,'input_bindings':255,'tools':2,'real_model_calls':0,'calibration_compile':8,'calibration_simulate':8})
put('delivery.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FROZEN_PENDING_COORDINATOR_RELEASE','review':'REVIEW.md','planned_slots':96,'real_model_calls':0,'production_reservations_created_by_preparer':0,'loopback_posts':104,'calibration_compile':8,'calibration_simulate':8,'source_lock_sha256':sha(P/'source-lock.json'),'runtime_excluded_from_packet':True})
files=[p for p in sorted(P.rglob('*')) if p.is_file() and 'runtime' not in p.relative_to(P).parts and p.name!='packet-lock.json']
put('packet-lock.json',{p.relative_to(P).as_posix():sha(p) for p in files})
assert all(sha(P/n)==h for n,h in read(P/'packet-lock.json').items())
print(json.dumps({'packet_files':len(files),'packet_sha256':sha(P/'packet-lock.json'),'source_lock_sha256':sha(P/'source-lock.json'),'verified':True,'real_model_calls':0}))
