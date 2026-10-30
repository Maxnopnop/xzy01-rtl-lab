import collections,hashlib,itertools,json
from decimal import Decimal as D
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
N=R/'exploration/20261029/rag20-five-model-proposal-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
locks=read(N/'review-lock.json');old=read(N/'old-evidence-snapshot.json')
assert all(sha(N/n)==h for n,h in locks.items())
assert all(sha(R/n)==h for n,h in old.items())
s=read(N/'proposal-slots.json');b=read(N/'budget.json');pol=read(N/'proposal-policy.json')
models=[m['id'] for m in b['models']];tasks=pol['task_ids'];conditions=sorted({x['condition'] for x in s})
assert len(s)==420 and len({x['id'] for x in s})==420
assert set((x['task'],x['model'],x['condition'],x['sample']) for x in s)==set(itertools.product(tasks,models,conditions,[1]))
assert all(x['status']=='NOT_STARTED' and x['reserved'] is False and x['executable'] is False for x in s)
rows=[]
for m in b['models']:
 pi=D(str(m['input_usd_per_million']));po=D(str(m['output_usd_per_million']))
 scenario=(D(20*8500)*pi+D(60*1500)*po)/D(1000000)
 cap=D(60*8192)*(pi+po)/D(1000000)
 assert scenario==D(str(m['scenario_usd'])) and cap==D(str(m['conditional_cap_usd']))
 ep=read(N/(m['id'].split('/')[-1]+'-endpoints.json'))['data']['endpoints']
 chosen=[x for x in ep if x['tag']==m['provider_tag']]
 assert chosen
 pricing=[x['pricing'] for x in chosen]
 applicable=[v for x in pricing for v in [x]+x.get('overrides',[]) if not v.get('min_prompt_tokens')]
 prices_match=max(D(str(x['prompt']))*1000000 for x in applicable)==pi and max(D(str(x['completion']))*1000000 for x in applicable)==po
 assert prices_match,m['id']
 rows.append({'model':m['id'],'scenario':str(scenario),'cap':str(cap),'exact_tag_prices':pricing,'price_match':prices_match,'supported_parameters':[x.get('supported_parameters') for x in chosen]})
scenario=sum(D(x['scenario']) for x in rows);cap=sum(D(x['cap']) for x in rows)
assert scenario==D(str(b['all_scenario_usd'])) and cap==D(str(b['all_conditional_cap_usd']))
assert cap*D('1.2')==D(str(b['with_20_percent_reserve']))
labels=read(N/'task-labels-copy.json')
assert labels==read(R/'exploration/20261023/public-rag-all20-v1/task-labels.json')
out={'review_files_verified':len(locks),'old_files_verified':len(old),'review_lock_sha256':sha(N/'review-lock.json'),'slots':len(s),'per_model':dict(collections.Counter(x['model'] for x in s)),'per_condition':dict(collections.Counter(x['condition'] for x in s)),'labels':dict(collections.Counter(x['current_label'] for x in labels)),'clear_ids':[x['id'] for x in labels if x['clear_subset']],'models':rows,'scenario_usd':str(scenario),'conditional_cap_usd':str(cap),'with_reserve_usd':str(cap*D('1.2')),'generation_calls':0,'embedding_calls':0,'network_calls':0,'eda_calls':0,'release':False}
(P/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='models'},ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False))
