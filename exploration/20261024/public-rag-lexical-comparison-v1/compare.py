"""Single-pass lexical scoring, no generation/embedding/network or HDL tools."""
import json,re,math,time,hashlib,datetime,importlib.util,itertools,statistics,socket,subprocess,sys
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,x):
    assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def deny(*a,**k):raise RuntimeError('Network/subprocess disabled in offline experiment')
socket.socket=deny;socket.create_connection=deny;subprocess.Popen=deny;subprocess.run=deny
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def terms(s):return re.findall(r'[a-z_][a-z0-9_]*',s.lower())
class TFIDF:
    def __init__(self,corpus):
        bags=[Counter(x) for x in corpus];vocab=set().union(*(set(x) for x in bags));N=len(bags)
        self.idf={t:math.log((1+N)/(1+sum(t in x for x in bags)))+1 for t in sorted(vocab)}
        self.docs=[self.vec(b) for b in bags]
    def vec(self,bag):
        w={t:(1+math.log(bag[t]))*self.idf[t] for t in sorted(bag) if t in self.idf};norm=math.sqrt(sum(x*x for x in w.values()))
        return {t:v/norm for t,v in w.items()} if norm else {}
    def get_scores(self,query):
        q=self.vec(Counter(query));return [sum(q[t]*d[t] for t in sorted(q.keys()&d.keys())) for d in self.docs]
def selected(rows):return [x['chunk_id'] for x in rows if x['eligible']][:3]
def score(index,query,chunks,bags):
    scores=index.get_scores(query);q=set(query)
    rows=[{'chunk_id':c['id'],'score':float(s),'eligible':bool(q&set(b))} for c,s,b in zip(chunks,scores,bags)]
    assert all(math.isfinite(x['score']) for x in rows)
    return sorted(rows,key=lambda x:(-x['score'],x['chunk_id']))
cfg=read(P/'protocol.json');lock=read(P/'protocol-lock.json');assert all(sha(P/n)==h for n,h in lock.items())
assert not(P/'results').exists(),'One-shot; never overwrite or repeat benchmark pass'
start=time.perf_counter();put(P/'results/start.json',{'utc':utc(),'protocol_sha256':sha(P/'protocol-lock.json'),'model_calls':0,'embedding_calls':0,'eda_calls':0})
bm=module('frozen_public_bm25',P/'upstream/rank_bm25.py');ref=module('reference_tfidf',P/'inputs/baseline_reference.py')
import numpy as np
ctors={'TFIDF_local':TFIDF,'BM25Okapi':bm.BM25Okapi,'BM25L':bm.BM25L,'BM25Plus':bm.BM25Plus}
# Generic software fixtures only, fixed before all real-query scoring.
toy=[{'id':f'T{i}','text':t} for i,t in enumerate(['apple pear','apple pear','orange','plum','lemon','lime','kiwi','grape'])]
tb=[terms(c['text']) for c in toy];tests={}
for name,ctor in ctors.items():
    index=ctor(tb);r=score(index,['apple'],toy,tb)
    tests[name+'_ties']=selected(r)==['T0','T1']
    tests[name+'_oov']=not selected(score(index,['zzzzzz'],toy,tb))
    tests[name+'_empty']=not selected(score(index,[],toy,tb))
truth=ref.retrieve('apple pear',toy);cached=TFIDF(tb).get_scores(['apple','pear']);truthmap={r['chunk_id']:r['score'] for r in truth['rankings']}
tests['cached_tfidf_matches_reference']=all(abs(cached[i]-truthmap[c['id']])<1e-12 for i,c in enumerate(toy))
tests['runtime_no_model_dependencies']=not any(x in sys.modules for x in ['torch','transformers','sentence_transformers','openai'])
put(P/'results/generic-check.json',{'checks':tests,'passed':all(tests.values()),'queries':'fruit fixture only'})
assert all(tests.values()),'Stop before benchmark; preserve failed fixtures'
chunks=read(P/'inputs/chunks.json');bags=[terms(c['text']) for c in chunks];queries=read(P/'inputs/query-manifest.json');indexes={};build={};records=[];reservations=[]
for name,ctor in ctors.items():
    t=time.perf_counter();indexes[name]=ctor(bags);build[name]=time.perf_counter()-t
template=(P/'inputs/context-template.txt').read_bytes().decode()
for query in queries:
    text=(P/query['file']).read_bytes().decode();tokens=terms(text)
    for name,index in indexes.items():
        assert time.perf_counter()-start<120
        reservation={'ordinal':len(reservations)+1,'task':query['id'],'method':name,'status':'RESERVED','utc':utc()};reservations.append(reservation)
        (P/'results/reservations.json').write_text(json.dumps(reservations,indent=2)+'\n',encoding='utf-8')
        t=time.perf_counter();ranks=score(index,tokens,chunks,bags);elapsed=time.perf_counter()-t;ids=selected(ranks)
        chosen=[next(c for c in chunks if c['id']==i) for i in ids]
        frag='\n\n'.join(f"[{c['id']}; lowRISC Verilog Coding Style Guide; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in chosen)
        context=template.format(fragments=frag) if chosen else ''
        rr={'task':query['id'],'method':name,'query_sha256':query['sha256'],'query_terms':tokens,'selected_ids':ids,'rankings':ranks,'selected_chunks':chosen,'context':context,'context_bytes':len(context.encode()),'query_seconds':elapsed,'status':'COMPLETE'}
        put(P/'results/retrieval'/f"{query['id']}__{name}.json",rr)
        records.append({k:rr[k] for k in ['task','method','selected_ids','context_bytes','query_seconds']});reservation['status']='COMPLETE'
        (P/'results/reservations.json').write_text(json.dumps(reservations,indent=2)+'\n',encoding='utf-8')
metrics={}
for name in ctors:
    rows=[r for r in records if r['method']==name];lengths=[r['context_bytes'] for r in rows]
    metrics[name]={'queries':len(rows),'no_hit':sum(not r['selected_ids'] for r in rows),'unique_chunks':len(set(i for r in rows for i in r['selected_ids'])),'mean_context_bytes':statistics.mean(lengths),'min_context_bytes':min(lengths),'max_context_bytes':max(lengths),'index_build_ms':build[name]*1000,'median_query_ms':statistics.median(r['query_seconds'] for r in rows)*1000}
pairs=[]
for a,b in itertools.combinations(ctors,2):
    values=[]
    for q in queries:
        x=next(r['selected_ids'] for r in records if r['task']==q['id'] and r['method']==a);y=next(r['selected_ids'] for r in records if r['task']==q['id'] and r['method']==b)
        values.append({'task':q['id'],'same_top1':x[:1]==y[:1],'same_order':x==y,'same_set':set(x)==set(y),'intersection_fraction':len(set(x)&set(y))/3,'jaccard':len(set(x)&set(y))/len(set(x)|set(y)) if x or y else 1})
    pairs.append({'a':a,'b':b,'same_top1':sum(v['same_top1'] for v in values),'same_order':sum(v['same_order'] for v in values),'same_set':sum(v['same_set'] for v in values),'mean_intersection_fraction':statistics.mean(v['intersection_fraction'] for v in values),'mean_jaccard':statistics.mean(v['jaccard'] for v in values),'per_query':values})
old=Path(cfg['preservation_root']);oldlock=read(old/'packet-lock.json');bad=[n for n,h in oldlock.items() if sha(old/n)!=h]
audit={'input_lock_unchanged':all(sha(P/n)==h for n,h in lock.items()),'old_packet_files_checked':len(oldlock),'old_mismatches':bad,'all80_complete':len(reservations)==80 and all(x['status']=='COMPLETE' for x in reservations),'unique_method_query_pairs':len({(x['task'],x['method']) for x in reservations})==80,'no_model_dependencies_loaded':not any(x in sys.modules for x in ['torch','transformers','sentence_transformers','openai'])}
put(P/'results/audit.json',audit);assert audit['input_lock_unchanged'] and not bad and audit['all80_complete'] and audit['unique_method_query_pairs'] and audit['no_model_dependencies_loaded']
put(P/'results/summary.json',{'utc':utc(),'scope':cfg['scope'],'retrievals':len(records),'model_calls':0,'embedding_calls':0,'eda_calls':0,'methods':metrics,'pairs':pairs,'records':records,'python':sys.version,'numpy':np.__version__,'latency_note':'one pass warm CPU observations; not statistically reliable performance benchmark; shared tokenizer outside timer, scoring/ranking included','relevance_metrics':None,'rtl_scores':None})
print(json.dumps({'retrievals':len(records),'metrics':metrics,'pairs':[{k:v for k,v in x.items() if k!='per_query'} for x in pairs],'audit':audit},ensure_ascii=False))
