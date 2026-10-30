import json,hashlib,datetime,re,shutil,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent;LAB=P.parents[2];OLD=LAB/'exploration/20261023/public-rag-all20-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def put(p,x):
    assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (P/'A').exists();A=P/'A';A.mkdir()
source=read(OLD/'A/corpus/manifest.json')['source'];src=OLD/'A/corpus/upstream/VerilogCodingStyle.md';lic=OLD/'A/corpus/upstream/LICENSE'
assert sha(src)==source['original_sha256'] and sha(lic)==source['license_sha256']
for f,name in [(src,'sources/VerilogCodingStyle.md'),(lic,'sources/LICENSE'),(OLD/'A/system.txt','system.txt'),(P/'retriever-source.py','retriever.py'),(P/'findings.md','DESIGN_BASIS.md')]:
    (A/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,A/name)
for name in ['tree.json','commit.json','dataset-README.md','dataset-LICENSE']:
    (A/'metadata').mkdir(exist_ok=True);shutil.copyfile(OLD/'A/metadata'/name,A/'metadata'/name)
spec=importlib.util.spec_from_file_location('generic',A/'retriever.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
chunks=m.chunk_document(src.read_bytes().decode('utf-8'))
put(A/'chunks.json',chunks)
put(A/'source-manifest.json',{'source_count':1,'chunk_count':len(chunks),'source':source,'origin':'Byte-identical cached public original, not old selected corpus; no fresh source HTTP','changes':'Whole document greedy contiguous lines<=2048characters; all content retained, no topic filter; slices may cross Markdown/code fences','authority':'Style guidance only, not normative LRM; generic examples may conflict with baseline allowed constructs, original task and baseline restrictions take precedence','cognitive_blinding':False,'task_based_design':False})
template='\n\n<generic_reference_context>\nThese are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.\nSource: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified contiguous excerpts.\n'+source['document_url']+'\n{fragments}\n</generic_reference_context>\n'
(A/'context-template.txt').write_bytes(template.encode())
put(A/'retrieval-policy.json',{'algorithm':'TF-IDF cosine','tf':'1+ln(count)','idf':'ln((1+N)/(1+df))+1','normalization':'L2, document vocabulary only','tokenizer':'[a-z_][a-z0-9_]* lower-case','stopwords':[],'stemming':False,'query_expansion':False,'synonyms':[],'max_chars_per_chunk':2048,'overlap':0,'max_chunks':60,'top_k':3,'minimum_score':'strictly >0','tie_break':'ascending chunk ID','query':'complete original prompt, no hand selected terms','no_hit':'empty context; no fallback','assembly':'system exact historical baseline; user=original bytes decoded + context only for rag','fragment':'[{id}; lowRISC Verilog Coding Style Guide; lines {start_line}-{end_line}] newline {text}','fragment_separator':'two newlines','design_input':'general algorithm/document only, no question/result based tuning'})
ex=read(OLD/'A/exclusions.json');hist=[]
for root in [LAB/'exploration',LAB/'benchmarks']:
    for f in sorted(root.rglob('*_prompt.txt')):
        if P in f.parents:continue
        if re.match(r'Prob\d+_',f.name):hist.append({'id':f.name.removesuffix('_prompt.txt'),'path':f.relative_to(LAB).as_posix(),'sha256':sha(f)})
exposed=sorted(set(ex['explicit_public_ids'])|{r['id'] for r in hist})
put(A/'history-exclusions.json',{'exposed_ids':exposed,'original_inventory':hist,'historical_tasks':ex['historical_tasks'],'additional_exposed_families':ex['additional_exposed_families'],'metadata_family_regex':ex['conservative_metadata_family_regex'],'use':'Exclusion only, never corpus/query/parameter design; all prior candidate sources count exposure regardless of result'})
policy=read(OLD/'A/selection-policy.json');paths={x['path']:x for x in read(A/'metadata/tree.json')['tree'] if x['type']=='blob'}
ids=sorted(p.removeprefix('dataset_spec-to-rtl/').removesuffix('_prompt.txt') for p in paths if p.startswith('dataset_spec-to-rtl/') and p.endswith('_prompt.txt'))
excluded=[];remaining=[]
for t in ids:
    reason='PRIOR_READ_OR_USED' if t in exposed else ('CONSERVATIVE_HISTORY_FAMILY' if re.search(ex['conservative_metadata_family_regex'],t,re.I) else None)
    if reason:excluded.append({'id':t,'reason':reason})
    else:remaining.append(t)
key=lambda t:(hashlib.sha256((policy['seed']+'\n'+t).encode()).hexdigest(),t)
ordered=sorted(remaining,key=key)
rows=[{'rank':i+1,'id':t,'order_sha256':key(t)[0],'files':{k:{'path':f'dataset_spec-to-rtl/{t}_{k}','git_blob_sha1':paths[f'dataset_spec-to-rtl/{t}_{k}']['sha']} for k in ['prompt.txt','ref.sv','test.sv']}} for i,t in enumerate(ordered[:20])]
put(P/'protocol/overlay.json',{'utc':utc(),'status':'PREPARATION_ONLY','dataset_commit':policy['commit'],'seed':policy['seed'],'metadata_total':len(ids),'metadata_exclusions':excluded,'remaining_ordered_ids':ordered,'new_candidates':rows,'max_candidates':20,'target_selected':8,'selection':'first up to8 statically eligible, all20 denominator; reject substantive historical/within-round near duplication or unresolved key contracts; same-repository ref only conditional; do not rank by retrieval or predicted model success; no refill','models':['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol'],'conditions':['no_rag','rag'],'samples':2,'max_planned_slots':96,'automatic_retries':0,'max_completion_tokens':None,'batch_wall_seconds':None,'request_timeout_seconds':180,'concurrency':1,'http_limit_bytes':1048576,'text_limit_bytes':131072,'max_job_disk_bytes':8388608,'max_run_disk_bytes':536870912,'source_get_cap':60,'source_timeout_seconds':30,'source_file_limit_bytes':524288,'source_total_limit_bytes':8388608,'stop':'First service/transport/protocol/unknown/hash/resource error stops; reservation consumes opportunity; no automatic continuation or replacement','preparation_eda':'Static review selected for this round; no compile/sim/SAT/synthesis executed. Any future reference validation separately proposed','task_order':'rank; no_rag,rag; luna,terra,sol; sample1,2','usage':'raw actual usage; absent fields null; no price invention','technical_release':False})
(P/'protocol/route.json').write_bytes((LAB/'exploration/20261023/openrouter-launch-v1/route.json').read_bytes())
put(P/'A-lock.json',{f.relative_to(A).as_posix():sha(f) for f in sorted(A.rglob('*')) if f.is_file()})
put(P/'protocol-lock.json',{f.relative_to(P/'protocol').as_posix():sha(f) for f in sorted((P/'protocol').rglob('*')) if f.is_file()})
put(P/'A-seal.json',{'frozen_utc':utc(),'a_lock_sha256':sha(P/'A-lock.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'source_count':1,'chunks':len(chunks),'new_candidate_content_reads':0,'cognitive_blind':False})
print(json.dumps({'chunks':len(chunks),'candidates':[r['id'] for r in rows],'excluded':len(excluded),'remaining':len(ordered),'new_task_content_reads':0}))
