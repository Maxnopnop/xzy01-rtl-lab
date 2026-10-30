import hashlib,json,datetime,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;LAB=P.parents[2];OLD=LAB/'exploration/20261023/public-rag-all20-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def put(p,v):
    assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (P/'A').exists()
lock=read(OLD/'A-lock.json');assert all(sha(OLD/'A'/k)==h for k,h in lock.items())
shutil.copytree(OLD/'A',P/'A');shutil.copyfile(OLD/'A-lock.json',P/'A-lock.json')
assert set(lock)=={p.relative_to(P/'A').as_posix() for p in (P/'A').rglob('*') if p.is_file()}
ex=read(P/'A/exclusions.json');hist=[]
for root in [LAB/'exploration',LAB/'benchmarks']:
    for f in sorted(root.rglob('*_prompt.txt')):
        if P in f.parents:continue
        if re.match(r'Prob\d+_',f.name):hist.append({'id':f.name.removesuffix('_prompt.txt'),'path':str(f.relative_to(LAB)),'sha256':sha(f)})
oldids=[r['id'] for r in read(OLD/'task-labels.json')]
exposed=sorted(set(ex['explicit_public_ids'])|set(oldids)|{r['id'] for r in hist})
put(P/'protocol/history-overlay.json',{'utc':utc(),'exposed_ids':exposed,'old20':oldids,'local_original_inventory':hist,'inherited_semantic_history':'A/exclusions.json historical_tasks and additional_exposed_families; review substantive overlap after reading candidates','rule':'Prior source presence conservatively counts exposure. No old scores used.'})
policy=read(P/'A/selection-policy.json');paths={x['path']:x for x in read(P/'A/metadata/tree.json')['tree'] if x['type']=='blob'}
ids=sorted(x.removeprefix('dataset_spec-to-rtl/').removesuffix('_prompt.txt') for x in paths if x.startswith('dataset_spec-to-rtl/') and x.endswith('_prompt.txt'))
excluded=[];eligible=[]
for i in ids:
    reason='PRIOR_EXPOSED_ID' if i in exposed else ('INHERITED_CONSERVATIVE_FAMILY' if re.search(ex['conservative_metadata_family_regex'],i,re.I) else None)
    if reason:excluded.append({'id':i,'reason':reason})
    else:eligible.append(i)
key=lambda x:(hashlib.sha256((policy['seed']+'\n'+x).encode()).hexdigest(),x)
ordered=sorted(eligible,key=key)
rows=[{'rank':n+1,'id':i,'order_sha256':key(i)[0],'files':{k:{'path':f'dataset_spec-to-rtl/{i}_{k}','git_blob_sha1':paths.get(f'dataset_spec-to-rtl/{i}_{k}',{}).get('sha')} for k in ['prompt.txt','ref.sv','test.sv']}} for n,i in enumerate(ordered[:20])]
overlay={'utc':utc(),'status':'PREPARATION_ONLY_NOT_RELEASED','seed':policy['seed'],'dataset_commit':policy['commit'],'max_candidates':20,'target_selected':12,'selection':'First12 statically eligible in fixed order; review all20; ambiguous key semantics/overlap excluded; no refill; correlated ref only conditional','metadata_exclusions':excluded,'remaining_ordered_ids':ordered,'new_candidates':rows,'http_max_requests':60,'timeout_seconds':30,'raw_file_limit_bytes':524288,'raw_total_limit_bytes':8388608,'retries':0,'models':['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol'],'wire_models':['openai/gpt-5.6-luna','openai/gpt-5.6-terra','openai/gpt-5.6-sol'],'conditions':['no_rag','rag'],'samples':2,'max_planned_slots':144,'schedule':'candidate rank; no_rag then rag; luna terra sol; sample1 then2','max_completion_tokens':None,'request_timeout_seconds':180,'concurrency':1,'batch_wall_limit_seconds':None,'response_text_limit_bytes':131072,'http_response_limit_bytes':1048576,'retry':0,'replacement_samples':0,'stop':'first service/transport/unknown/model-provider mismatch/hash drift/resource error; unknown reservation consumes opportunity; no resend or automatic continuation','usage':'actual input/output/reasoning/cache/cost; missing null; raw usage retained','route_source':str(LAB/'exploration/20261023/openrouter-launch-v1/route.json'),'counts':'new independent plan, not additive to old240 or prior216 proposals; no production ledger','preparation_model_calls':0,'preparation_eda_calls':0}
put(P/'protocol/overlay.json',overlay)
shutil.copyfile(LAB/'exploration/20261023/openrouter-launch-v1/route.json',P/'protocol/route.json')
put(P/'protocol-lock.json',{p.relative_to(P/'protocol').as_posix():sha(p) for p in sorted((P/'protocol').rglob('*')) if p.is_file()})
put(P/'A-seal.json',{'frozen_utc':utc(),'a_lock_sha256':sha(P/'A-lock.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'original_a_lock_sha256':sha(OLD/'A-lock.json'),'new_content_reads':0,'candidate_ids':[r['id'] for r in rows]})
print(json.dumps({'candidate_ids':[r['id'] for r in rows],'metadata_total':len(ids),'excluded':len(excluded),'remaining':len(ordered),'a_hash':sha(P/'A-lock.json')}))
