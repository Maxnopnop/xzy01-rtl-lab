import json,hashlib,datetime,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=P.parent/'public-rag-independent-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(P/'inputs').exists() and not(P/'protocol-lock.json').exists()
adopt=P.parent/'public-rag-all20-reconsider-v1/adoption.json';a=json.loads(adopt.read_bytes())
assert a['task_count']==20 and all(r['adopted'] for r in a['rows'])
oldlock=json.loads((OLD/'packet-lock.json').read_bytes());assert all(sha(OLD/n)==h for n,h in oldlock.items())
(P/'inputs/queries').mkdir(parents=True)
queries=[]
for row in a['rows']:
    src=OLD/row['source_bindings']['prompt.txt']['local'];dest=P/'inputs/queries'/f"{row['id']}.txt"
    assert sha(src)==row['source_bindings']['prompt.txt']['sha256'];shutil.copyfile(src,dest)
    queries.append({'id':row['id'],'rank':row['rank'],'file':dest.relative_to(P).as_posix(),'sha256':sha(dest)})
for src,name in [('A/chunks.json','chunks.json'),('A/context-template.txt','context-template.txt'),('A/sources/LICENSE','corpus-LICENSE'),('A/retriever.py','baseline_reference.py')]:shutil.copyfile(OLD/src,P/'inputs'/name)
put(P/'inputs/query-manifest.json',queries)
put(P/'protocol.json',{'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'OFFLINE_LEXICAL_COMPONENT_COMPARISON_NOT_FULL_RAG_REPRODUCTION','public_source':'https://github.com/dorianbrown/rank_bm25','commit':json.loads((P/'upstream/commit.json').read_bytes())['sha'],'license':'Apache-2.0','methods':{'TFIDF_local':{'tf':'1+ln(count)','idf':'ln((1+N)/(1+df))+1','norm':'L2','implementation':'new cached adapter of existing generic formula; toy-only conformance check'},'BM25Okapi':{'k1':1.5,'b':0.75,'epsilon':0.25},'BM25L':{'k1':1.5,'b':0.75,'delta':0.5},'BM25Plus':{'k1':1.5,'b':0.75,'delta':1}},'parameter_basis':'upstream default constructors, not tuned on queries; no claim these equal Elasticsearch defaults','tokenizer':'[a-z_][a-z0-9_]* lowercase, no stopwords/stemming/query expansion; query multiplicity retained','corpus':'same frozen48 complete-document lowRISC chunks; chunk text only, same for all','queries':'same20 adopted raw prompts; no ref/TB/outcome use','selection':'eligible iff shared token with query; sort full score descending then ID ascending; up to3; no numeric score threshold; empty if no lexical match','selection_reason':'uniform nonmatch exclusion because BM25L/Plus include nonzero baseline terms; not calibrated using benchmark results','context':'same frozen template and fragment format; complete chosen chunks; no adaptive token clipping','execution':'single pass20queries x4methods=80; eachmethod/query exactlyonce; no rerun/tuning; no generation/embedding/EDA/network in runner','metrics':['full rankings/rawscores retained but scores not compared across algorithms','top1 agreement','top3 ordered/set agreement','top3 intersection fraction and Jaccard','unique retrieved chunks','context UTF8bytes','index build time and single-pass warm query time separately'], 'not_metrics':['relevance accuracy','nDCG/recall without independent qrels','RTL correctness','RAG benefit','winner selection'], 'limits':'20 queries,48 docs,4 methods,top3; max process120s; local outputs only; no package installation','adoption_sha256':sha(adopt),'source_packet_lock_sha256':sha(OLD/'packet-lock.json'),'preservation_root':str(OLD)})
files=[p for folder in ['inputs','upstream'] for p in (P/folder).rglob('*') if p.is_file()]+[P/n for n in ['protocol.json','compare.py','freeze.py','fetch_public.py','access.json']]
put(P/'protocol-lock.json',{p.relative_to(P).as_posix():sha(p) for p in sorted(files)})
print(json.dumps({'queries':len(queries),'methods':4,'planned_retrievals':80,'lock_sha256':sha(P/'protocol-lock.json')}))
