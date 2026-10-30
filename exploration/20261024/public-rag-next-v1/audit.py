"""Read-only assertions over sealed stages. Never retrieves, invokes HDL or HTTP."""
import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent;LAB=P.parents[2]
def read(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def check(cond,msg):
    if not cond:raise AssertionError(msg)
def validate_request(obj,messages,model,route):
    check(set(obj)=={'model','messages','stream','provider'},'request fields')
    check(obj['messages']==messages,'message drift');check(obj['model']=='openai/'+model,'model drift')
    check(obj['stream'] is False,'stream')
    check(obj['provider']=={'only':route['provider_only'],'allow_fallbacks':False,'require_parameters':True},'route drift')
out={};cfg=read(P/'protocol/overlay.json');route=read(P/'protocol/route.json');sel=read(P/'B/selection.json')
for name in ['A','B','C','protocol']:
    lock=read(P/(name+'-lock.json'));check(set(lock)=={x.relative_to(P/name).as_posix() for x in (P/name).rglob('*') if x.is_file()},name+' inventory')
    check(all(sha(P/name/k)==h for k,h in lock.items()),name+' hashes');out[name+'_files']=len(lock)
check(all(sha(P/k)==v for k,v in read(P/'plan-lock.json').items()),'plan lock')
old=LAB/'exploration/20261023/public-rag-all20-v1';check((P/'A-lock.json').read_bytes()==(old/'A-lock.json').read_bytes(),'A byte lock reuse')
check(all((P/'A'/k).read_bytes()==(old/'A'/k).read_bytes() for k in read(P/'A-lock.json')),'A bytes exact')
a=read(P/'A-seal.json');b=read(P/'B-seal.json');c=read(P/'C-seal.json')
check(a['frozen_utc']<read(P/'B/start.json')['utc']<read(P/'B/fetch-complete.json')['utc']<b['frozen_utc']<read(P/'C/start.json')['utc']<c['frozen_utc'],'stage chronology')
for n,s in [('A',a),('B',b),('C',c)]:check(s[n.lower()+'_lock_sha256']==sha(P/(n+'-lock.json')),'seal binding '+n)
visits=read(P/'B/access.json');check(len(visits)==60 and len({x['url'] for x in visits})==60,'GET cap/unique')
check(sum(x['bytes'] for x in visits)<=8388608,'total source cap')
for r in visits:
    raw=(P/r['local']).read_bytes();check(len(raw)<=524288 and digest(raw)==r['sha256'],'raw SHA')
    check(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['actual_git_blob']==r['expected_git_blob'],'git blob')
exposed=set(read(P/'protocol/history-overlay.json')['exposed_ids'])
check(not exposed.intersection(x['id'] for x in cfg['new_candidates']),'exposure IDs')
check(len(sel['rows'])==20 and sel['selected_ids']==[r['id'] for r in sel['rows'] if r['eligible']][:12],'selection fixed order')
chunks=read(P/'A/corpus/chunks.json');by={x['id']:x for x in chunks};check(len(chunks)==18,'chunks')
system=(P/'A/system.txt').read_bytes().decode();template=(P/'A/context-template.txt').read_bytes().decode('utf-8-sig');slots=read(P/'C/slots.json');groups={};expected=[]
for row in sel['rows']:
    if not row['selected']:continue
    task=row['id'];raw=(P/row['bindings']['prompt.txt']['local']).read_bytes();q=raw.decode();rr=read(P/'C/retrieval'/f'{task}.json')
    check(rr['query'].encode()==raw and rr['query_sha256']==digest(raw),'retrieval original query')
    ranks=rr['rankings'];check(len(ranks)==18 and ranks==sorted(ranks,key=lambda x:(-x['score'],x['chunk_id'])),'rank order')
    ids=[r['chunk_id'] for r in ranks if r['score']>0][:3];check(rr['selected_ids']==ids,'top3 no manual replace')
    check(rr['selected_chunks']==[by[i] for i in ids],'chunk exact')
    fragments='\n\n'.join(f"[{x['id']}; {x['section']}; lines {x['start_line']}-{x['end_line']}]\n{x['text']}" for x in [by[i] for i in ids])
    context=template.format(fragments=fragments) if ids else '';check((P/'C/contexts'/f'{task}.txt').read_bytes()==context.encode(),'context exact')
    for cond in cfg['conditions']:
        messages=[{'role':'system','content':system},{'role':'user','content':q+(context if cond=='rag' else '')}]
        check(read(P/'C/messages'/f'{task}__{cond}.json')==messages,'messages assembly')
        for model in cfg['models']:
            for sample in [1,2]:
                expected.append(f'{task}__{cond}__{model}__s{sample:03d}')
                slot=slots[len(expected)-1];check(slot['id']==expected[-1] and slot['ordinal']==len(expected),'slot order')
                req=read(P/slot['request']);validate_request(req,messages,model,route)
                check(sha(P/slot['request'])==slot['request_sha256'],'request hash')
                req.pop('model');groups.setdefault((task,cond),[]).append(req)
check(len(slots)==len(expected)==len(sel['selected_ids'])*12==96,'slot count')
check(all(len(g)==6 and all(x==g[0] for x in g) for g in groups.values()),'cross model/sample equality')
check(all(s['status']=='NOT_STARTED' and not s['reserved'] for s in slots),'zero execution')
# Deliberately corrupt IN-MEMORY fixture only. No files, model/EDA, retrieval or old matrix runs.
fixture=read(P/slots[0]['request']);messages=fixture['messages'];negative=[]
for field in ['model','messages','provider','max_completion_tokens']:
    bad=json.loads(json.dumps(fixture))
    if field=='model':bad[field]='another/model'
    elif field=='messages':bad[field][1]['content']+=' altered'
    elif field=='provider':bad[field]['allow_fallbacks']=True
    else:bad[field]=8192
    try:validate_request(bad,messages,slots[0]['model'],route)
    except AssertionError:negative.append(field)
check(len(negative)==4,'negative audit catches drift')
pres=[]
for name in ['public-rag-all20-v1','public-rag-holdout-v1','direct-api-v1','cli-cache-repair-v1']:
    root=LAB/'exploration/20261023'/name;lock=read(root/'packet-lock.json');bad=[k for k,v in lock.items() if sha(root/k)!=v];check(not bad,'old packet '+name)
    pres.append({'packet':name,'entries':len(lock),'mismatches':bad,'lock_sha256':sha(root/'packet-lock.json')})
out.update(status='OFFLINE_PREPARATION_SELF_CHECK_PASS_NOT_EXECUTION_RELEASE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_gets=60,source_bytes=sum(x['bytes'] for x in visits),source_blob_matches=60,candidates=20,selected_conditional=8,excluded=12,groups=len(groups),requests=96,retrievals=8,retrieval_not_reexecuted_in_audit=True,negative_fixture_rejections=negative,old_preservation=pres,model_calls=0,eda_calls=0,independent_correctness_passes=0)
(P/'self-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
