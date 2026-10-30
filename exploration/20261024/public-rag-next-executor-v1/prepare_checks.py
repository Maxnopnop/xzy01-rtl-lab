import json,re,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent/'public-rag-next-v1';OLD=P.parents[1]/'20261023/openrouter-launch-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(n,x):
    p=P/n;assert not p.exists(),n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
script=(OLD/'Start-FirstThree.ps1').read_text().replace("'launch.py'","'runner.py'")
(P/'Start-Experiments.ps1').write_text(script,encoding='utf-8')
put('input-lock.json',{str(B/k):v for k,v in dict(read(B/'packet-lock.json'),**{'packet-lock.json':sha(B/'packet-lock.json')}).items()})
tasks=read(B/'plan.json')['task_order'];aliases={}
for task in tasks:
    raw=(B/'B/originals/dataset_spec-to-rtl'/f'{task}_ref.sv').read_bytes();assert raw.count(b'module RefModule')==1
    alias=raw.replace(b'module RefModule',b'module TopModule',1);dest=P/'calibration-inputs'/f'{task}.sv';dest.parent.mkdir(exist_ok=True);dest.write_bytes(alias);aliases[task]={'path':dest.relative_to(P).as_posix(),'sha256':sha(dest),'transform':'Only first module name RefModule -> TopModule; original reference retained unchanged'}
put('source-lock.json',{n:sha(P/n) for n in ['core.py','ledger.py','runner.py','transport.py','usage.py','Start-Experiments.ps1','tools-lock.json','route.json']})
put('calibration-plan.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tasks':tasks,'aliases':aliases,'compile_cap':8,'simulate_cap':8,'per_compile_seconds':15,'per_simulate_seconds':10,'total_wall_seconds':300,'total_disk_bytes':67108864,'source_lock_sha256':sha(P/'source-lock.json'),'input_lock_sha256':sha(P/'input-lock.json'),'first_nonpass_stop':True,'retry':0,'independent_oracle':False,'model_calls':0})
put('offline-test-plan.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'success_loopback_slots':96,'failure_modes':['400','403','429','502','embedded502','redirect','interrupted','timeout'],'max_loopback_posts':104,'failure_reentry_expected_extra_posts':0,'fixture_key':'OFFLINE_SYNTHETIC_TOKEN_ONLY','http_external_generation':0,'resource_tests':['128KiB+1 text stops before extract/judge','128KiB exact admitted to extraction','tool timeout stops','TB TIMEOUT text stops','compile error remains result','HTTP body limit envelope stops'],'ledger_tests':['cap96','repeat complete ledger','unfinished reservation UNKNOWN no resend','hash drift','exclusive lock','identity mismatch','absence of batch wall cap'],'static_checks':'transport byte copy, usage_record/clean_env/bounded_process/extract AST correspondence; all96wirebytes directly frozen','no_old_matrix_rerun':True})
print('source/input and finite checks frozen')
