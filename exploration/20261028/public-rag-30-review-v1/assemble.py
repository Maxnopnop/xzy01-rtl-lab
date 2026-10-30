"""One frozen TF-IDF pass per candidate, data-only v3 draft, no inference."""
import datetime,hashlib,importlib.util,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def rawput(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
assert not (P/'retrieval-start.json').exists(),'No reretrieval or regeneration'
scope=read(P/'scope.json');reviews=read(P/'reference-risk-review.json');rows=reviews['rows']
alock=read(P/'prior/A-lock.json');assert all(sha(P/'A'/n)==h for n,h in alock.items())
put(P/'retrieval-start.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':sha(P/'scope.json'),'risk_review_sha256':sha(P/'reference-risk-review.json'),'A_lock_sha256':sha(P/'prior/A-lock.json'),'count_before':0,'fixed_denominator':30})
spec=importlib.util.spec_from_file_location('frozen48',P/'A/retriever.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
chunks=read(P/'A/chunks.json');assert len(chunks)==48
system=(P/'A/system.txt').read_bytes().decode();template=(P/'A/context-template.txt').read_bytes().decode()
prior=R/'exploration/20261024/openrouter-model-rag-proposal-v1';access=read(prior/'access.json')
models=[];metadata_review=[]
for mid in scope['models']:
 name=mid.split('/')[1];source=next(x for x in access if x['file']==name+'-endpoints.json')
 raw=(prior/source['file']).read_bytes();assert digest(raw)==source['sha256']
 path='metadata/'+source['file'];rawput(P/path,raw)
 ms='metadata/'+name+'-source.json'
 put(P/ms,{'source_url':source['url'],'retrieved_utc':source['utc'],'sha256':source['sha256'],'method':'GET','authenticated':False,'inference_availability':'NOT_VERIFIED','reused_local_snapshot':True,'new_GETs':0})
 params={'reasoning':{'effort':'medium'}} if name=='gpt-5.6-luna' else {}
 endpoint=[e for e in json.loads(raw)['data']['endpoints'] if e.get('tag')=='openai' and e.get('provider_name')=='OpenAI'];assert len(endpoint)==1 and endpoint[0]['status']==0
 assert set(params)<=set(endpoint[0]['supported_parameters'])
 note='calls_only，无token cap/temperature/seed；Luna显式medium，其余无reasoning；默认采样与内部计算量未对齐。目录为10月24快照，仅字段支持证据，不证明账户/当前路由可用或RTL能力。'
 models.append({'id':mid,'author_namespace':'openai','provider_tag':'openai','response_provider':'OpenAI','parameters':params,'endpoint_metadata':path,'metadata_source':ms,'comparison_note':note})
 metadata_review.append({'id':mid,'selected_endpoint':endpoint[0],'parameter_field_supported':True,'reasoning_value_basis':'cached catalog reasoning.supported_efforts includes medium' if params else 'no reasoning parameter','inference_availability':'UNKNOWN','rtl_ability':'UNKNOWN','snapshot_age_days':4})
for n in ('catalog.json','selected-models.json','access.json'):rawput(P/'metadata'/('prior-'+n),(prior/n).read_bytes())
put(P/'metadata-review.json',metadata_review)
slots=[];retrieval_summary=[]
rawput(P/'contexts/empty.txt',b'')
for review in rows:
 task=review['id'];query=(P/next(x['local'] for x in review['source_bindings'] if x['kind']=='prompt.txt')).read_bytes().decode()
 rr=m.retrieve(query,chunks);chosen=[next(c for c in chunks if c['id']==n) for n in rr['selected_ids']]
 fragments='\n\n'.join(f"[{c['id']}; lowRISC Verilog Coding Style Guide; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in chosen)
 context=template.format(fragments=fragments) if chosen else ''
 rr.update(selected_chunks=chosen,context_sha256=digest(context.encode()),A_lock_sha256=sha(P/'prior/A-lock.json'))
 put(P/'retrieval'/f'{task}.json',rr);rawput(P/'contexts'/f'{task}.txt',context.encode())
 retrieval_summary.append({'task':task,'selected_ids':rr['selected_ids'],'scores':[x['score'] for x in rr['rankings'][:3]],'no_hit':rr['no_hit'],'context_bytes':len(context.encode()),'category_before_retrieval':review['category']})
 for arm in scope['conditions']:
  msgs=[{'role':'system','content':system},{'role':'user','content':query+(context if arm=='rag' else '')}]
  mf=f'messages/{task}__{arm}.json';put(P/mf,msgs)
  if review['category']=='DO_NOT_EXECUTE' or review['calibration']['expected_checks'] is None or review['assets_detected']:continue
  for model in models:
   for sample in (1,2):
    sid=f"rag30v1-{task}-{arm}-{model['id'].split('/')[1]}-s{sample}"
    request={'model':model['id'],'messages':msgs,'stream':False,'provider':{'only':[model['provider_tag']],'allow_fallbacks':False,'require_parameters':True},**model['parameters']}
    request_path=f'requests/{sid}.json';put(P/request_path,request)
    files={x['kind']:x['local'] for x in review['source_bindings']}
    slots.append({'ordinal':len(slots)+1,'id':sid,'task':task,'condition':arm,'model':model['id'],'sample':sample,'request':request_path,'messages_file':mf,'retrieved_file':f'contexts/{task}.txt' if arm=='rag' else 'contexts/empty.txt','spec':files['prompt.txt'],'reference':files['ref.sv'],'testbench':files['test.sv'],'expected_checks':review['calibration']['expected_checks'],'expected_checks_source':f'calibration/{task}/simulate.json','analysis_category':review['category'],'related_family':review['related_family'],'assets':[],'top':'TopModule','status':'NOT_STARTED','reserved':False})
put(P/'retrieval-summary.json',retrieval_summary)
# Bind all data consumed by import plus raw logs/decisions, not executable preparation scripts.
files={f.relative_to(P).as_posix():sha(f) for directory in ('A','originals','metadata','messages','contexts','requests','retrieval') for f in (P/directory).rglob('*') if f.is_file()}
for name in ('scope.json','scope-seal.json','v3-source-lock.json','reference-risk-review.json','metadata-review.json','retrieval-start.json','retrieval-summary.json','calibration/receipt-audit.json'):
 files[name]=sha(P/name)
for row in rows:
 for n in ('compile.json','simulate.json','result.json','reservation.json'):
  name=f"calibration/{row['id']}/{n}";files[name]=sha(P/name)
manifest={'schema':'console-frozen-v3','purpose':'DRAFT_REVIEW','name':'public-rag-30-review-20261028-v1','budget_policy':'calls_only','models':models,'max_calls':len(slots),'candidate_opportunity_ceiling':360,'source_revision_lock':'v3-source-lock.json','source_revision_lock_sha256':sha(P/'v3-source-lock.json'),'slots':slots,'files':files,'automatic_retries':0,'automatic_expansion':False,'request_timeout_seconds':180,'concurrency':1,'max_tokens':None,'max_cost_usd':None,'no_token_cap_field_sent':True,'model_calls':0,'usage':None,'cost':None,'unresolved':['user review of model combination','main vs auxiliary inclusion','calls_only has no token/dollar hard cap; fees require explicit user understanding','cached endpoint/current account availability UNKNOWN; no probe','same-source reference and sampling phase limits','school counts may differ; no school execution or gate-level validation'],'excluded_review_only':[x['id'] for x in rows if x['category']=='DO_NOT_EXECUTE'],'main_candidates':[x['id'] for x in rows if x['category']=='MAIN_CANDIDATE'],'auxiliary_candidates':[x['id'] for x in rows if x['category']=='AUXILIARY'],'release_created':False,'final_user_selection':False}
put(P/'console-package.json',manifest)
put(P/'assembly-summary.json',{'candidate_count':30,'review_only_no_slots':len(manifest['excluded_review_only']),'main_candidate_count':len(manifest['main_candidates']),'auxiliary_count':len(manifest['auxiliary_candidates']),'draft_opportunities':len(slots),'main_only_opportunities':len(manifest['main_candidates'])*12,'ceiling':360,'retrievals':len(retrieval_summary),'no_hits':sum(x['no_hit'] for x in retrieval_summary),'model_calls':0,'school_calls':0,'console_package_sha256':sha(P/'console-package.json'),'requests_have_no_token_cap':True})
print(read(P/'assembly-summary.json'))
