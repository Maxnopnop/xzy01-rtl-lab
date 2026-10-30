"""All20 addendum preparation; original A/B/C and old evidence stay untouched."""
from pathlib import Path
import json,hashlib,datetime,importlib.util,sys,shutil,time,re
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;OLD=P.parent/'public-rag-holdout-v1';ROOT=P.parents[2]
read=lambda p:json.loads(p.read_bytes().decode('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,obj):
 p=P/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
lock=read(OLD/'packet-lock.json');assert all(sha(OLD/k)==v for k,v in lock.items());assert sha(OLD/'packet-lock.json')=='9e14e8f0b53b6bc81caee003c01bf45b6cc4bae17170ac98259511866957be27'
assert not (P/'A').exists()
shutil.copytree(OLD/'A',P/'A');shutil.copyfile(OLD/'A-lock.json',P/'A-lock.json');shutil.copytree(OLD/'B/originals',P/'originals')
review=ROOT/'validation/RAG_FINAL_SELECTION_REVIEW_20261023.md';(P/'coordinator-semantic-review.md').write_bytes(review.read_bytes())
put('prior-bindings.json',{'prior_packet_path':str(OLD/'packet-lock.json'),'prior_packet_sha256':sha(OLD/'packet-lock.json'),'prior_bound_files':lock,'a_lock_sha256':sha(OLD/'A-lock.json'),'semantic_review_sha256':sha(review),'prior_60_slots_remain_not_started':True})
put('authorization-scope.json',{'utc':utc(),'basis':'Coordinator relay of newer direct human authorization: all previously ordered20 tasks, not only5; three named5.6 models, RAG/noRAG and2 samples.','scope':'Exactly previous B/selection.json20 rows, no new tasks','model_attempt_cap':240,'replaces_not_stacks_prior_proposals':True,'user_testing_intent_authorized':True,'technical_release':'Coordinator review of verified gates still required; no demo/unsupported route dispatch','school':'User-assisted later only; no platform action now','current_activity':'PREPARATION; model generation not started','calibration_permission':'Necessary finite original-reference tool calibration, predeclare limits and retain all failures, no task repair/retries'})
rows=read(OLD/'B/selection.json')['rows'];assert len(rows)==20
sp=importlib.util.spec_from_file_location('all20_frozen_retriever',P/'A/retriever.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
chunks=read(P/'A/corpus/chunks.json');by={x['id']:x for x in chunks};template=(P/'A/context-template.txt').read_bytes().decode('utf-8-sig');system=(P/'A/system.txt').read_bytes().decode();budget=read(P/'A/budget-policy.json')
oldselected=read(OLD/'B/selection.json')['selected_ids'];tags=[];slots=[];retrievals=[];doc=['# 固定20题执行补充包（模型生成尚未启动）\n','范围来自用户最新授权：旧B全部20题，不再筛选或补题。240是总尝试上限，替代旧60/24/30方案。全部题测试不等于全部合格holdout。原参考一致性与合规清晰两题子集分别报告。\n','A文件、检索器、参数、包装原字节复用。仅外层数量预算明确从5题60槽改为20题240槽，A/budget-policy.json保留为历史原件，当前数量以本包execution-policy.json为准。\n']
ambig={'Prob089_ece241_2014_q5a':'AMBIGUOUS_RESET_OUTPUT','Prob146_fsm_serialdata':'AMBIGUOUS_ERROR_RECOVERY_DONE','Prob064_vector3':'UNSPECIFIED_CONCAT_SPLIT_ORDER'}
clear=['Prob023_vector100r','Prob032_vector0']
for row in rows:
 task=row['id'];raw=(P/'originals/dataset_spec-to-rtl'/f'{task}_prompt.txt').read_bytes();q=raw.decode();assert hashlib.sha256(raw).hexdigest()==row['bindings']['prompt.txt']['sha256']
 newtag=ambig.get(task,'CONFIRMED_CLEAR_SUBSET' if task in clear else ('HISTORY_OR_SPEC_EXCLUDED' if not row['eligible'] else 'OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET'))
 tags.append({'rank':row['rank'],'id':task,'original_eligible':row['eligible'],'original_status':row['status'],'original_code':row['code'],'original_reason':row['reason_zh'],'current_label':newtag,'report_scope':'ALL20_REFERENCE_AGREEMENT','clear_subset':task in clear,'all20_holdout_claim':False})
 if task in oldselected:
  rr=read(OLD/'C/retrieval'/f'{task}.json');context=(OLD/'C/contexts'/f'{task}.txt').read_bytes().decode();mode='EXACT_REUSE_PRIOR_FROZEN_RESULT';seconds=0.
  (P/'retrieval').mkdir(exist_ok=True);(P/'retrieval'/f'{task}.json').write_bytes((OLD/'C/retrieval'/f'{task}.json').read_bytes())
 else:
  start=time.perf_counter();rr=m.retrieve(q,chunks);seconds=time.perf_counter()-start
  selected=[by[i] for i in rr['selected_ids']];frag='\n\n'.join(f"[{c['id']}; {c['section']}; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in selected)
  context=template.format(fragments=frag) if selected else '';rr.update(selected_chunks=selected,elapsed_seconds=seconds,a_lock_sha256=sha(P/'A-lock.json'),task_source_sha256=hashlib.sha256(raw).hexdigest(),context_sha256=hashlib.sha256(context.encode()).hexdigest());put('retrieval/'+task+'.json',rr);mode='NEW_FROZEN_AUTOMATIC_RETRIEVAL'
 (P/'contexts').mkdir(exist_ok=True);(P/'contexts'/f'{task}.txt').write_bytes(context.encode())
 retrievals.append({'task':task,'mode':mode,'selected_ids':rr['selected_ids'],'no_hit':rr['no_hit'],'new_seconds':seconds,'result_sha256':sha(P/'retrieval'/f'{task}.json')})
 for condition in budget['conditions']:
  user=q+(context if condition=='rag' else '');messages=[{'role':'system','content':system},{'role':'user','content':user}]
  if task in oldselected:assert messages==read(OLD/'C/messages'/f'{task}__{condition}.json')
  put('messages/'+f'{task}__{condition}.json',messages)
  for model in budget['models']:
   for sample in [1,2]:
    sid=f'{task}__{condition}__{model}__s{sample:03d}';request={'model':model,'messages':messages,'stream':False,'max_completion_tokens':8192};put('requests/'+sid+'.json',request)
    slots.append({'id':sid,'ordinal':len(slots)+1,'task':task,'condition':condition,'model':model,'sample':sample,'status':'NOT_STARTED','reserved':False,'request':'requests/'+sid+'.json','request_sha256':sha(P/'requests'/f'{sid}.json'),'messages_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()})
 doc.extend([f"\n## {row['rank']}. {task} — {row['meaning_zh']}\n",f"标签：{newtag}；原标签：{row['status']} / {row['code']}。\n",'原依据：'+row['reason_zh']+'\n',('总控后续语义裁决覆盖原条件性解释，见coordinator-semantic-review.md。\n' if task in ambig else ''),f"[原题]({row['bindings']['prompt.txt']['url']}) / [参考]({row['bindings']['ref.sv']['url']}) / [测试]({row['bindings']['test.sv']['url']})；MIT，固定commit。\n",'原题SHA256：'+hashlib.sha256(raw).hexdigest()+'\n','```text\n'+q+'```\n',f"自动检索：{', '.join(rr['selected_ids'])}；{mode}；完整18排名/逐词分数/全文见retrieval/{task}.json，完整实际拟消息见messages/{task}__rag.json和__no_rag.json。\n"])
 for cid in rr['selected_ids']:
  c=by[cid];score=next(x['score'] for x in rr['rankings'] if x['chunk_id']==cid);doc.append(f"\n{cid}，score={score!r}，{c['section']}，L{c['start_line']}-{c['end_line']}，SHA {c['sha256']}\n\n```text\n{c['text']}\n```\n")
 # Separate reference alias: original source bytes remain unchanged. No generated answer.
 ref=(P/'originals/dataset_spec-to-rtl'/f'{task}_ref.sv').read_bytes().decode();header=re.search(r'\bmodule RefModule\s*\(.*?\);',ref,re.S);assert header,task
 wrapper=header.group().replace('module RefModule','module TopModule',1)+'\n  RefModule reference_alias(.*);\nendmodule\n'
 (P/'reference-aliases').mkdir(exist_ok=True);(P/'reference-aliases'/f'{task}.sv').write_bytes(wrapper.encode())
put('task-labels.json',tags);put('retrieval-manifest.json',retrievals);put('slots.json',slots)
assert len(slots)==240
policy=dict(budget);policy.update(max_tasks=20,model_call_ceiling=240,completion_token_ceiling=1966080,task_order=[r['id'] for r in rows],schedule='fixed task rank, no_rag then rag, luna then terra then sol, sample1 then2; no result-adaptive order',counts_replacement='20task authorization replaces old5task proposal; all old packets unchanged',generation_permission='Intent authorized, technical gates BLOCKED until coordinator verification',calibration_cap={'compile':20,'simulate':20,'per_compile_seconds':15,'per_sim_seconds':10,'total_seconds':600,'max_per_case_disk_bytes':8388608,'max_total_disk_bytes':262144000,'stdout_or_stderr_limit_bytes':2097152,'concurrency':1,'stop':'First compile/sim/timeout/unknown/hash/resource/badreceipt failure stops whole calibration; no repair/retry','kind':'Same RefModule via TopModule alias, tool/harness smoke only, not independent oracle or model score'},future_calibration_proposal=None)
put('execution-policy.json',policy)
put('calibration-plan.json',{'utc':utc(),'task_order':[r['id'] for r in rows],'limits':policy['calibration_cap'],'input_bindings':{p.relative_to(P).as_posix():sha(p) for folder in ['originals','reference-aliases'] for p in sorted((P/folder).rglob('*')) if p.is_file()},'tools':{str(p):sha(p) for p in [Path('D:/iverilog/bin/iverilog.exe'),Path('D:/iverilog/bin/vvp.exe')]},'environment':'New child-only environment sets explicit COMSPEC/SystemRoot and System32+Icarus PATH based on prior diagnosed missing interpreter. No default regression rerun or proxy changes.','pass_rule':'both phases exit0, no limits/timeout/TIMEOUT text, exactly one Mismatches n in m samples with n=0,m>0; alias agreement not functional independence','model_calls':0})
put('ledger.json',{'utc':utc(),'max_attempts':240,'reserved':0,'complete_returns':0,'unknown':0,'failed':0,'not_started':240,'model_calls':0,'usage':{'input_tokens':0,'output_tokens':0,'cost_incurred_this_batch':0,'future_cost':'UNKNOWN provider and rates unconfigured'},'rule':'reserve+fsync before any send; UNKNOWN never resent; every attempted send consumes240 opportunity; no side probe calls','dispatcher_status':'NOT_IMPLEMENTED_PENDING_REAL_PROVIDER_CONTRACT; prepared240requests are not live dispatcher','model_execution_started':False})
(P/'ALL20_REVIEW.md').write_bytes('\n'.join(doc).encode())
put('preparation-summary.json',{'utc':utc(),'tasks':20,'original_files':60,'prior_retrieval_reused':5,'new_retrievals':15,'a_original_byte_copy':True,'requests':240,'new_input_sources':0,'new_http_downloads':0,'model_calls':0,'eda_calls_so_far':0,'clear_subset':clear,'full20_is_holdout':False,'remaining':'Calibration, offline audit, technical blockers, coordinator review'})
print(json.dumps(read(P/'preparation-summary.json')))
