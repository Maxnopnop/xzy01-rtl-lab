"""Read-only independent byte and cohort audit; never imports the runner."""
import collections, hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent
R=P.parents[1]
N=R/'exploration/20261029/main36-proxy-newbatch-v1'
O=R/'exploration/20261028/public-rag-30-review-v1'
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
checks['old_evidence_unchanged']=all(sha(R/n)==h for n,h in read(P/'baseline.json').items())
checks['frozen_packet_874_unchanged']=all(sha(O/n)==h for n,h in read(O/'packet-lock.json').items())
b=read(N/'batch.json'); old=read(O/'console-package-main36.json')
assert len(b['slots'])==len(old['slots'])==36
checks['new36_total38']=b['new_max_calls']==36 and b['cumulative_max_opportunities']==38
checks['models_unchanged']=b['models']==old['models']
checks['all_input_files_unchanged']=all(sha(N/'inputs'/n)==sha(O/n)==h for n,h in old['files'].items())
rows=[]
for a,z in zip(b['slots'],old['slots']):
 assert a['parent_slot_id']==z['id'] and a['id']!=z['id'] and a['ordinal']==z['ordinal']
 raw=(N/'inputs'/a['request']).read_bytes()
 assert raw==(O/z['request']).read_bytes()
 req=json.loads(raw)
 assert req['model']==a['model']
 assert not any(k in req for k in ('max_tokens','max_completion_tokens'))
 assert req['provider']['allow_fallbacks'] is False
 rows.append({'ordinal':a['ordinal'],'id':a['id'],'parent_id':z['id'],'request_sha256':hashlib.sha256(raw).hexdigest()})
checks['exact_request_bytes_36']=len(rows)==36
checks['unique_new_ids']=len({r['id'] for r in rows})==36
groups=collections.defaultdict(list)
for s in b['slots']:
 groups[(s['task'],s['condition'])].append(json.loads((N/'inputs'/s['request']).read_bytes())['messages'])
checks['same_complete_messages_each_condition']=len(groups)==6 and all(len(g)==6 and all(v==g[0] for v in g) for g in groups.values())
checks['all_new_unreserved']=all(not (Path(b['global_reservations'])/(s['id']+'.json')).exists() for s in b['slots'])
out={'passed':all(checks.values()),'checks':checks,'rows':rows,'network_requests':0,'model_calls':0,'eda_runs':0}
(P/'binding-audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'passed':out['passed'],'checks':checks},indent=2))
assert out['passed']

