"""Read-only comparison of existing real runs. No execution/retrieval/network."""
import json,hashlib,re,statistics,datetime
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).resolve().parent;LAB=P.parents[2];evidence={}
def raw(p):
    p=Path(p);b=p.read_bytes();evidence[str(p)]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def digest(b):return hashlib.sha256(b).hexdigest()
def norm(b):
    s=b.decode('utf-8');s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S);return re.sub(r'\s+','',s)
def put(p,x):
    assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
batches=[('old240',LAB/'exploration/20261023/public-rag-all20-v1','slots.json','contexts','retrieval',[LAB/'exploration/20261023/direct-api-v1/runtime/live-run',LAB/'validation/openrouter-resume84-v1/runtime/continuation',LAB/'validation/openrouter-resume198-v1/runtime/continuation']),('next96',LAB/'exploration/20261024/public-rag-next-v1','C/slots.json','C/contexts','C/retrieval',[LAB/'exploration/20261024/public-rag-next-executor-v1/runtime/live-run'])]
reports={}
for batch,base,slotfile,contextdir,retrievaldir,runs in batches:
    slots=read(base/slotfile);pairs=defaultdict(dict);groups=defaultdict(Counter);bytask=defaultdict(Counter);rows=[];requests={};code={};jobdirs={};checks=Counter();usage=defaultdict(list)
    for s in slots:
        locations=[root for root in runs if (root/'results'/f"{s['id']}.json").exists()]
        assert locations,s['id'];resultbytes=[raw(root/'results'/f"{s['id']}.json") for root in locations];assert len(set(resultbytes))==1
        r=json.loads(resultbytes[0]);assert r['mode']=='LIVE'
        owners=[root for root in locations if (root/'jobs'/f"{s['ordinal']:03d}"/'request.json').exists()];assert len(owners)==1,(s['id'],owners)
        job=owners[0]/'jobs'/f"{s['ordinal']:03d}";jobdirs[s['id']]=job
        requestbytes=raw(job/'request.json');req=json.loads(requestbytes);frozen=read(base/s['request'])
        assert req['messages']==frozen['messages'] and digest(requestbytes)==r['request_sha256'];checks['actual_request_messages_match_frozen']+=1
        tr=read(job/'transport-response.json');assert tr['request_sha256']==r['request_sha256'];checks['transport_bound_to_actual_request']+=1
        assert tr['client_post_invocations']==1;checks['single_client_post']+=1
        requests[s['id']]=req
        user=req['messages'][1]['content'];assert req['messages'][0]['role']=='system' and req['messages'][1]['role']=='user'
        if s['condition']=='rag':
            context=raw(base/contextdir/f"{s['task']}.txt").decode();assert context and user.endswith(context);checks['rag_has_exact_nonempty_context']+=1
        if (job/'dut.sv').exists():code[s['id']]=raw(job/'dut.sv')
        status=r['status'];groups[s['model']+'/'+s['condition']][status]+=1;bytask[s['task']][s['condition']+'_pass']+=status=='REFERENCE_PASS'
        pairs[(s['task'],s['model'],s['sample'])][s['condition']]=dict(slot=s['id'],status=status)
        row={k:s[k] for k in ['ordinal','id','task','model','sample','condition']};row.update(status=status,job=str(job),rtl_sha256=digest(code[s['id']]) if s['id'] in code else None,request_sha256=digest(requestbytes),request_keys=sorted(req))
        if r.get('usage') and isinstance(r['usage'].get('prompt_tokens'),int):usage[s['condition']].append(r['usage']['prompt_tokens'])
        if status in ['REFERENCE_PASS','REFERENCE_FAIL']:
            log=raw(job/'simulate.stdout.bin').decode();m=re.findall(r'^Mismatches: (\d+) in (\d+) samples$', '\n'.join(log.splitlines()),re.M);assert len(m)==1
            errors,samples=map(int,m[0]);assert samples>0 and (errors==0)==(status=='REFERENCE_PASS');row.update(mismatches=errors,samples=samples);checks['simulation_status_reparsed']+=1
        rows.append(row)
    paired=Counter();outcomes=[]
    for (task,model,sample),pair in pairs.items():
        a=pair['no_rag'];b=pair['rag'];qa=requests[a['slot']];qb=requests[b['slot']]
        assert qa['messages'][0]==qb['messages'][0]
        context=raw(base/contextdir/f'{task}.txt').decode();assert qb['messages'][1]['content']==qa['messages'][1]['content']+context;checks['paired_exact_original_plus_context']+=1
        if a['status'].startswith('SERVICE') or b['status'].startswith('SERVICE'):kind='service_unpaired'
        else:
            ap=a['status']=='REFERENCE_PASS';bp=b['status']=='REFERENCE_PASS';kind='both_pass' if ap and bp else 'both_nonpass' if not ap and not bp else 'help' if bp else 'worse'
        paired[kind]+=1
        available=a['slot'] in code and b['slot'] in code
        rr={'task':task,'model':model,'sample':sample,'category':kind,'no_rag':a,'rag':b,'rtl_both_available':available,'exact_rtl_equal':code[a['slot']]==code[b['slot']] if available else None,'comment_whitespace_equal':norm(code[a['slot']])==norm(code[b['slot']]) if available else None}
        outcomes.append(rr)
    task_info={}
    for task,counts in bytask.items():
        retrieval=read(base/retrievaldir/f'{task}.json');task_info[task]={'pass_counts':dict(counts),'selected_ids':retrieval['selected_ids'],'no_hit':retrieval['no_hit'],'context_bytes':len(raw(base/contextdir/f'{task}.txt'))}
    reports[batch]={'slots':len(slots),'groups':{k:dict(v) for k,v in groups.items()},'paired':dict(paired),'checks':dict(checks),'code_comparison':{'paired_total':len(outcomes),'both_rtl_available':sum(x['rtl_both_available'] for x in outcomes),'exact_equal':sum(x['exact_rtl_equal'] is True for x in outcomes),'comment_whitespace_equal':sum(x['comment_whitespace_equal'] is True for x in outcomes),'note':'Text normalization only; not AST or functional equivalence'},'input_tokens':{k:{'reported_count':len(v),'sum':sum(v),'mean':statistics.mean(v)} for k,v in usage.items()},'tasks':task_info,'pairs':outcomes,'rows':rows,'request_keys':sorted({tuple(x['request_keys']) for x in rows})}
assert all(digest(Path(n).read_bytes())==h for n,h in evidence.items())
put(P/'audit.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'batches':reports,'evidence_files_unchanged':len(evidence),'model_calls':0,'embedding_calls':0,'retrieval_calls':0,'eda_calls':0,'network_calls':0,'limitations':['paired sample numbers do not establish common random seed','pass under original TB is not full correctness','normalization equality not formal equivalence','request keys cannot establish provider internals','no hypotheses proven causally; no method modifications']})
put(P/'evidence-lock.json',evidence)
print(json.dumps({batch:{k:v for k,v in r.items() if k not in ['pairs','rows','tasks']} for batch,r in reports.items()},ensure_ascii=False))
