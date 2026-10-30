"""Read-only artifact audit; writes a new audit receipt only. No EDA/network."""
from pathlib import Path
import json,hashlib,re,datetime,zipfile,math,collections,importlib.util,sys,csv
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
read=lambda p:json.loads(p.read_bytes().decode('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for s in 'ABC':
 lock=read(P/f'{s}-lock.json')
 assert set(lock)=={p.relative_to(P/s).as_posix() for p in (P/s).rglob('*') if p.is_file()}
 assert all(sha(P/s/k)==h for k,h in lock.items())
 assert sha(P/f'{s}-lock.json')==read(P/f'{s}-seal.json')[s.lower()+'_lock_sha256']
 checks[s+'_lock']={'count':len(lock),'sha256':sha(P/f'{s}-lock.json'),'status':'PASS'}
aseal=read(P/'A-seal.json');bseal=read(P/'B-seal.json');cs=read(P/'C/start.json')
assert aseal['frozen_utc']<read(P/'B/start.json')['utc']<=read(P/'B/fetch-start.json')['utc']<read(P/'B/fetch-complete.json')['utc']<bseal['frozen_utc']<cs['utc']
checks['phase_order']='PASS local UTC receipts+hash bindings; not external notarization'
policy=read(P/'A/selection-policy.json');ex=read(P/'A/exclusions.json');order=read(P/'B/candidate-order.json');sel=read(P/'B/selection.json')
ids=sorted(x['path'].split('/')[-1].removesuffix('_prompt.txt') for x in read(P/'A/metadata/tree.json')['tree'] if x['path'].startswith('dataset_spec-to-rtl/') and x['path'].endswith('_prompt.txt'))
remaining=[i for i in ids if i not in ex['explicit_public_ids'] and not re.search(ex['conservative_metadata_family_regex'],i,re.I)]
remaining.sort(key=lambda i:(hashlib.sha256((policy['seed']+'\n'+i).encode()).hexdigest(),i))
assert remaining==order['remaining_ordered_ids']
assert remaining[:20]==[r['id'] for r in order['new_candidates']]==[r['id'] for r in sel['rows']]
assert sel['selected_ids']==[r['id'] for r in sel['rows'] if r['eligible']][:5]
assert not set(sel['selected_ids'])&set(ex['explicit_public_ids'])
checks['selection']='PASS deterministic metadata/first5 declared-eligible; semantic judgments require coordinator review'
visits=read(P/'B/access.json');assert len(visits)==60 and len({v['url'] for v in visits})==60
for v in visits:
 raw=(P/'B'/v['local']).read_bytes();assert v['status']=='SAVED' and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==v['git_blob_expected'] and hashlib.sha256(raw).hexdigest()==v['sha256']
checks['sources']={'requests':60,'raw_bytes':sum(v['bytes'] for v in visits),'saved':60,'failed':0,'retry':0,'git_blob_and_sha256':'PASS'}
spec=importlib.util.spec_from_file_location('audit_frozen_retrieval',P/'A/retriever.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
chunks=read(P/'A/corpus/chunks.json');chunkby={c['id']:c for c in chunks}
# Independent scorer, with fixed declared constants/token set and tie rules.
stop=set('a an the and or of to in for with on as is are be by from this that it its use using only each at after before when then do not must should'.split())
def tokens(s):return [x for x in re.findall('[a-z][a-z0-9_]*',s.lower()) if x not in stop]
bags=[collections.Counter(tokens(c['section']+'\n'+c['text'])) for c in chunks];lens=[sum(b.values()) for b in bags];avg=sum(lens)/len(lens)
for task in sel['selected_ids']:
 raw=(P/'B/originals/dataset_spec-to-rtl'/f'{task}_prompt.txt').read_bytes();q=raw.decode();rr=read(P/'C/retrieval'/f'{task}.json')
 ranking=[]
 for c,bag,dl in zip(chunks,bags,lens):
  score=0.
  for term in sorted(set(tokens(q))):
   if term in bag:
    df=sum(term in b for b in bags);tf=bag[term]
    score+=math.log(1+(len(chunks)-df+0.5)/(df+0.5))*(tf*2.2)/(tf+1.2*(1-0.75+0.75*dl/avg))
  ranking.append((c['id'],score))
 ranking.sort(key=lambda r:(-r[1],r[0]))
 assert ranking==[(r['chunk_id'],r['score']) for r in rr['rankings']]
 assert rr['selected_ids']==[r[0] for r in ranking if r[1]>0][:3]
 frag='\n\n'.join(f"[{chunkby[i]['id']}; {chunkby[i]['section']}; lines {chunkby[i]['start_line']}-{chunkby[i]['end_line']}]\n{chunkby[i]['text']}" for i in rr['selected_ids'])
 context=(P/'A/context-template.txt').read_bytes().decode('utf-8-sig').format(fragments=frag) if rr['selected_ids'] else ''
 assert (P/'C/contexts'/f'{task}.txt').read_bytes()==context.encode()
 assert (P/'C/users'/f'{task}__no_rag.txt').read_bytes()==raw
 assert (P/'C/users'/f'{task}__rag.txt').read_bytes()==raw+context.encode()
 assert b'```text\n'+raw+b'```' in (P/'USER_REVIEW.md').read_bytes()
 with zipfile.ZipFile(P/'selected-original-prompts.zip') as z:assert z.read(task+'_prompt.txt')==raw
checks['retrieval_independent_recalculation']='PASS all5 full18 rankings and exact context'
assert m.retrieve('zzzzzznonexistenttoken',chunks)['no_hit']
fixture=[dict(id='ZZ2',section='alpha',text='gamma'),dict(id='ZZ1',section='alpha',text='gamma')]
assert m.retrieve('alpha',fixture)['selected_ids']==['ZZ1','ZZ2']
checks['fixed_nohit_tie_fixtures']='PASS generic synthetic words only, no method change'
slots=read(P/'C/slots.json');assert len(slots)==60 and len({s['id'] for s in slots})==60
for task in sel['selected_ids']:
 for condition in ['no_rag','rag']:
  group=[s for s in slots if s['task']==task and s['condition']==condition];assert len(group)==6
  messages=read(P/'C/messages'/f'{task}__{condition}.json')
  for slot in group:
   req=read(P/slot['request']);assert req==dict(model=slot['model'],messages=messages,stream=False,max_completion_tokens=8192)
   assert sha(P/slot['request'])==slot['request_sha256'] and slot['status']=='NOT_STARTED'
checks['proposed_requests']='PASS 60 slots, 10 message pairs, all6 copies identical within task-condition; actual service unverified'
prior=[]
for relative in ['exploration/20261016/public-benchmark-rag-v1','exploration/20261016/fixed-input-rag-v2']:
 base=ROOT/relative;lock=read(base/'packet-lock.json');bad=[k for k,h in lock.items() if not (base/k).is_file() or sha(base/k)!=h];assert not bad,bad
 prior.append(dict(path=relative,files=len(lock),packet_sha256=sha(base/'packet-lock.json'),status='PASS'))
for relative in ['exploration/20261016/fixed-input-rag-v2/baseline-bindings.json','exploration/20261023/public-rag-holdout-v1/A/reuse-bindings.json']:
 lock=read(ROOT/relative);assert all(sha(ROOT/k)==h for k,h in lock.items());prior.append(dict(path=relative,files=len(lock),status='PASS'))
checks['prior_preservation']=prior
# Only whitelisted config fields: never read credentials into receipt/output.
with (ROOT/'config.local.models.csv').open(encoding='utf-8-sig',newline='') as f:
 rows=list(csv.DictReader(f));cols=list(rows[0]) if rows else []
checks['routing_static']={'columns_allowlisted':[k for k in cols if k.lower() in ['enabled','model','model_id','name']],'rows':[{k:v for k,v in row.items() if k.lower() in ['enabled','model','model_id','name']} for row in rows],'status':'UNVERIFIED no probe or API call'}
checks['current_execution']={'model':0,'embedding':0,'rerank':0,'compile':0,'sim':0,'sat':0,'proxy_regression_reruns':0}
out=P/'audit.json';assert not out.exists();out.write_bytes((json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS_STATIC_PREPARATION_ONLY',checks=checks,remaining='Coordinator semantic qualification review, actual transport/budget/model support, independent correctness, new task checker adaptation remain blocked.'),ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(checks,ensure_ascii=False))
