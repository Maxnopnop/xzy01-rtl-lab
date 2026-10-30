import json, hashlib, re
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
from datetime import datetime, timezone

OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
EXE=LAB/'exploration/20261024/public-rag-next-executor-v1'
B=LAB/'exploration/20261024/public-rag-next-v1'
RUN=EXE/'runtime/live-run'
evidence={}
def raw(p):
    p=Path(p); b=p.read_bytes(); evidence[str(p)]=hashlib.sha256(b).hexdigest(); return b
def read(p): return json.loads(raw(p))
def sha(p): return hashlib.sha256(raw(p)).hexdigest()
def lock(p,base=None):
    d=read(p)
    for name,h in d.items(): assert sha(base/name if base else Path(name))==h,name
    return len(d)
checks={}
for name,base in [('source',EXE),('input',None),('tools',None)]:
    checks[name+'_lock_entries']=lock(EXE/(name+'-lock.json'),base)
checks['packet_lock_entries']=lock(B/'packet-lock.json',B)
assert sha(EXE/'source-lock.json')=='fc24d8895d897ee9ace9facb398d991c8110e47ed4cd6b6a4bcd50dd1d14f78c'
assert sha(B/'packet-lock.json')=='a8f24bd42a5b3d6bf3b4a7f12732dc9aa6f601347862f5538be61243677fecee'
slots=read(B/'C/slots.json')
assert len(slots)==96
assert len(list((RUN/'results').glob('*.json')))==len(list((RUN/'reservations').glob('*.json')))==96
assert not (RUN/'STOP.json').exists() and not (RUN/'exclusive.lock').exists()
counts=Counter(); arms=defaultdict(Counter); pairs=defaultdict(dict); groups=defaultdict(list)
usage=Counter(); cost=Decimal(0); failures=[]; rows=[]
for s in slots:
    job=RUN/'jobs'/f'{s["ordinal"]:03d}'
    r=read(RUN/'results'/f'{s["id"]}.json')
    read(RUN/'reservations'/f'{s["id"]}.json')
    assert raw(job/'request.json')==raw(B/s['request'])
    assert sha(job/'request.json')==s['request_sha256']==r['request_sha256']
    req=read(job/'request.json'); assert req.pop('model')==s['wire_model']
    groups[(s['task'],s['condition'],s['sample'])].append(req)
    tr=read(job/'transport-response.json'); body=tr['body'].encode()
    assert hashlib.sha256(body).hexdigest()==tr['raw_body_sha256']
    assert tr['client_post_invocations']==1 and tr['http_status']==200
    assert tr['request_sha256']==s['request_sha256']
    response=json.loads(body)
    assert response['model']==r['response_model']==s['wire_model']
    assert response['provider']==r['reported_provider']=='OpenAI'
    assert r['usage']==response['usage'] and r['complete_http_return'] and r['mode']=='LIVE' and not r['stop']
    assert raw(job/'reference.sv')==raw(B/'B/originals/dataset_spec-to-rtl'/f'{s["task"]}_ref.sv')
    assert raw(job/'testbench.sv')==raw(B/'B/originals/dataset_spec-to-rtl'/f'{s["task"]}_test.sv')
    for i,phase in enumerate(('compile','simulate')):
        receipt=read(job/f'{phase}-receipt.json')
        assert receipt==r['phases'][i]
        assert receipt['returncode']==0 and receipt['limit_reason'] is None and receipt['launch_error'] is None
        for channel in ('stdout','stderr'): assert sha(job/f'{phase}.{channel}.bin')==receipt[channel+'_sha256']
    log=raw(job/'simulate.stdout.bin').decode()
    m=re.findall(r'^Mismatches: (\d+) in (\d+) samples$', '\n'.join(log.splitlines()),re.M)
    assert len(m)==1
    mismatches,total=map(int,m[0]); assert total>0
    assert r['receipt']==[[mismatches,total]]
    assert r['status']==('REFERENCE_PASS' if mismatches==0 else 'REFERENCE_FAIL')
    counts[r['status']]+=1; arms[(s['model'],s['condition'])][r['status']]+=1
    pairs[(s['task'],s['model'],s['sample'])][s['condition']]=r['status']
    u=response['usage']
    usage.update(input_tokens=u['prompt_tokens'],output_tokens=u['completion_tokens'],total_tokens=u['total_tokens'],reasoning_tokens=u['completion_tokens_details']['reasoning_tokens'],cached_input_tokens=u['prompt_tokens_details']['cached_tokens'])
    cost+=Decimal(str(u['cost']))
    row={k:s[k] for k in ('ordinal','task','model','condition','sample')}
    row.update(status=r['status'],mismatches=mismatches,checked_samples=total,utc=r['utc'])
    rows.append(row)
    if mismatches: failures.append(row)
assert len(groups)==32 and all(len(v)==3 and v[0]==v[1]==v[2] for v in groups.values())
paired=Counter(); paired_model=defaultdict(Counter); changes=[]
for (task,model,sample),p in pairs.items():
    assert set(p)=={'no_rag','rag'}
    a=p['no_rag']=='REFERENCE_PASS'; b=p['rag']=='REFERENCE_PASS'
    kind='both_pass' if a and b else 'both_fail' if not a and not b else 'helped' if b else 'worsened'
    paired[kind]+=1; paired_model[model][kind]+=1
    if a!=b:changes.append(dict(task=task,model=model,sample=sample,kind=kind))
checks.update(request_byte_matches=96,reported_model_provider_matches=96,single_client_posts=96,compile_simulation_log_matches=96,identical_three_model_groups=32)
# Detect writes during the audit without changing evidence.
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in evidence.items())
report=dict(utc=datetime.now(timezone.utc).isoformat(),status='VERIFIED',model_calls=0,network_requests=0,eda_calls=0,checks=checks,counts=dict(counts),arms={f'{m}/{c}':dict(v) for (m,c),v in arms.items()},paired=dict(paired),paired_by_model={m:dict(v) for m,v in paired_model.items()},changes=changes,failures=failures,usage=dict(usage),reported_cost_sum=str(cost),cost_currency='not inferred',rows=rows,limitations=['same-source reference; not independent oracle','Prob143 testbench does not cover multi-hot states','related task families; 8 tasks are not 8 independent families','two samples per task/model/condition; no general RAG benefit established','client logs cannot establish hidden provider-side execution or retries'])
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'evidence-lock.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False,indent=2))
