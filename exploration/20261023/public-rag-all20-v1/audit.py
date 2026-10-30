"""Audit all20 artifacts without model/network/EDA execution."""
from pathlib import Path
import json,hashlib,sys,importlib.util,re,datetime
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;OLD=P.parent/'public-rag-holdout-v1'
read=lambda p:json.loads(p.read_bytes().decode('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results={}
for k,v in read(OLD/'packet-lock.json').items():assert sha(OLD/k)==v
assert {p.relative_to(OLD).as_posix() for p in OLD.rglob('*') if p.is_file()}==set(read(OLD/'packet-lock.json'))|{'packet-lock.json','seal-verification.json'}
results['prior_packet']={'status':'PASS','sha256':sha(OLD/'packet-lock.json'),'files':len(read(OLD/'packet-lock.json'))}
a=read(P/'A-lock.json');assert a==read(OLD/'A-lock.json');assert set(a)=={p.relative_to(P/'A').as_posix() for p in (P/'A').rglob('*') if p.is_file()};assert all(sha(P/'A'/k)==h for k,h in a.items());results['A_exact_copy']='PASS30files no method changes'
pre=read(P/'pre-execution-lock.json');assert all(sha(P/k)==h for k,h in pre.items());assert sha(P/'pre-execution-lock.json')==read(P/'pre-execution-seal.json')['lock_sha256'];results['pre_execution_source_lock']={'status':'PASS','files':len(pre)}
assert read(P/'pre-execution-seal.json')['utc']<read(P/'calibration-v1/started.json')['utc']
rows=read(OLD/'B/selection.json')['rows'];tasks=[r['id'] for r in rows];labels=read(P/'task-labels.json');assert tasks==[r['id'] for r in labels]
for row,label in zip(rows,labels):
 assert row['reason_zh']==label['original_reason'] and row['status']==label['original_status'] and row['code']==label['original_code']
 for kind,b in row['bindings'].items():
  path=P/'originals/dataset_spec-to-rtl'/f"{row['id']}_{kind}";assert sha(path)==b['sha256']
results['originals_and_labels']='PASS all60 original files and all20 original status/reasons; later3 ambiguities separately labelled'
chunks=read(P/'A/corpus/chunks.json');template=(P/'A/context-template.txt').read_bytes().decode('utf-8-sig');system=(P/'A/system.txt').read_bytes().decode();by={c['id']:c for c in chunks}
sp=importlib.util.spec_from_file_location('frozen_audit',P/'A/retriever.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
oldtasks=read(OLD/'B/selection.json')['selected_ids'];manifest=read(P/'retrieval-manifest.json');assert sum(r['mode']=='NEW_FROZEN_AUTOMATIC_RETRIEVAL' for r in manifest)==15
for task in tasks:
 raw=(P/'originals/dataset_spec-to-rtl'/f'{task}_prompt.txt').read_bytes();q=raw.decode();r=read(P/'retrieval'/f'{task}.json');expected=m.retrieve(q,chunks)
 for key in ['query','query_sha256','query_terms','rankings','selected_ids','no_hit']:assert r[key]==expected[key],(task,key)
 if task in oldtasks:assert (P/'retrieval'/f'{task}.json').read_bytes()==(OLD/'C/retrieval'/f'{task}.json').read_bytes()
 frag='\n\n'.join(f"[{by[i]['id']}; {by[i]['section']}; lines {by[i]['start_line']}-{by[i]['end_line']}]\n{by[i]['text']}" for i in r['selected_ids']);ctx=template.format(fragments=frag) if r['selected_ids'] else '';assert (P/'contexts'/f'{task}.txt').read_bytes()==ctx.encode()
 for condition in ['no_rag','rag']:
  messages=read(P/'messages'/f'{task}__{condition}.json');assert messages==[dict(role='system',content=system),dict(role='user',content=q+(ctx if condition=='rag' else ''))]
 assert b'```text\n'+raw+b'```' in (P/'ALL20_REVIEW.md').read_bytes()
results['retrieval_and_messages']='PASS5byte-reused+15new deterministic retrievals; full20 ranks/contexts and40messages exact'
slots=read(P/'slots.json');assert len(slots)==240 and len({s['id'] for s in slots})==240
for task in tasks:
 for condition in ['no_rag','rag']:
  group=[s for s in slots if s['task']==task and s['condition']==condition];assert len(group)==6 and len({s['messages_sha256'] for s in group})==1
  for s in group:
   assert s['status']=='NOT_STARTED' and not s['reserved'];assert sha(P/s['request'])==s['request_sha256']
   assert read(P/s['request'])==dict(model=s['model'],messages=read(P/'messages'/f'{task}__{condition}.json'),stream=False,max_completion_tokens=8192)
results['240_proposals']='PASS same task-condition content across3models2samples; allNOT_STARTED; no actual transport proof'
cal=P/'calibration-v1';ev=read(cal/'evidence-lock.json');assert all(sha(cal/k)==h for k,h in ev.items());assert {p.relative_to(cal).as_posix() for p in cal.rglob('*') if p.is_file()}==set(ev)|{'evidence-lock.json'}
summary=read(cal/'summary.json');assert summary['compile_attempts']==20 and summary['sim_attempts']==20 and len(summary['results'])==20
for r in summary['results']:
 assert r['status']=='HARNESS_SMOKE_PASS' and r['original_receipt'][0][0]==0 and r['original_receipt'][0][1]>0
 for phase in r['phases']:
  folder=cal/r['task'];assert sha(folder/(phase['stage']+'.stdout.bin'))==phase['stdout_sha256'];assert sha(folder/(phase['stage']+'.stderr.bin'))==phase['stderr_sha256'];assert phase['returncode']==0 and not phase['limit_reason']
results['calibration']={'status':'PASS_HARNESS_ONLY','compile':20,'simulate':20,'reference_independence':False,'model_score':False,'nonzero_sample_tasks':20,'reported_total_samples':sum(r['original_receipt'][0][1] for r in summary['results']),'source_bytes':'original files copied exactly, TopModule alias separate','evidence_files':len(ev),'no_retries':True}
ledger=read(P/'ledger.json');assert ledger['reserved']==ledger['unknown']==ledger['model_calls']==0 and ledger['not_started']==240
results['ledger']='PASS initial240unstarted, zero reservations/calls/charges; live dispatcher not implemented or authorized by technical review'
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_ARTIFACT_AND_TOOL_SMOKE_AUDIT_NOT_EXECUTION_RELEASE','checks':results,'model_calls':0,'new_eda_calls':{'compile':20,'simulate':20,'SAT':0},'not_proven':['independent functional correctness','unambiguous specs for20','model service support','actual hidden wrapper equality','enforced output budget','finite production dispatcher readiness']}
assert not (P/'audit.json').exists();(P/'audit.json').write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps(record,ensure_ascii=False))
