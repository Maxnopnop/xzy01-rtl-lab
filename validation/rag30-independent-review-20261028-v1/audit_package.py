"""Independent retrieval/request audit, guarded data-only console import, no calls."""
import hashlib,json,math,re,sys
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P=ROOT/'exploration/20261028/public-rag-30-review-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn'):
        raise RuntimeError('READ_ONLY_AUDIT_NO_NETWORK_OR_SUBPROCESS: '+event)
sys.addaudithook(guard)

def main():
    prior=read(HERE/'input-audit.json')
    for n,h in prior['evidence_sha256'].items():assert sha(P/n)==h,n
    risk=read(P/'reference-risk-review.json');start=read(P/'retrieval-start.json')
    assert start['risk_review_sha256']==sha(P/'reference-risk-review.json')
    assert start['scope_sha256']==sha(P/'scope.json')
    categories=Counter(r['category'] for r in risk['rows'])
    assert dict(categories)==risk['categories']=={'MAIN_CANDIDATE':3,'AUXILIARY':22,'DO_NOT_EXECUTE':5}
    chunks=read(P/'A/chunks.json');byid={c['id']:c for c in chunks}
    assert len(chunks)==48 and ''.join(c['text'] for c in chunks)==(P/'A/sources/VerilogCodingStyle.md').read_bytes().decode()
    tokens=lambda text:re.findall(r'[a-z_][a-z0-9_]*',text.lower())
    bags=[Counter(tokens(c['text'])) for c in chunks]
    vocab=set().union(*map(set,bags))
    idf={w:1+math.log((1+len(bags))/(1+sum(w in bag for bag in bags))) for w in vocab}
    def vec(bag):
        w={t:(1+math.log(n))*idf[t] for t,n in bag.items() if t in idf}
        norm=math.sqrt(math.fsum(v*v for v in w.values()))
        return {t:v/norm for t,v in w.items()} if norm else {}
    vectors=[vec(b) for b in bags];expected_messages={};retrieval_results=[]
    system=(P/'A/system.txt').read_bytes().decode();template=(P/'A/context-template.txt').read_bytes().decode()
    for row in risk['rows']:
        task=row['id'];query=(P/'originals/dataset_spec-to-rtl'/f'{task}_prompt.txt').read_bytes().decode()
        r=read(P/'retrieval'/f'{task}.json');q=vec(Counter(tokens(query)))
        scores={c['id']:math.fsum(v.get(t,0)*w for t,w in q.items()) for c,v in zip(chunks,vectors)}
        order=sorted(scores,key=lambda k:(-scores[k],k));top=[k for k in order if scores[k]>0][:3]
        assert r['query']==query and r['selected_ids']==top
        assert [x['chunk_id'] for x in r['rankings']]==order
        assert all(abs(x['score']-scores[x['chunk_id']])<1e-12 for x in r['rankings'])
        assert r['selected_chunks']==[byid[k] for k in top]
        fragments='\n\n'.join(f"[{c['id']}; lowRISC Verilog Coding Style Guide; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in [byid[k] for k in top])
        context=template.format(fragments=fragments) if top else ''
        assert (P/'contexts'/f'{task}.txt').read_bytes()==context.encode()
        assert sha(P/'contexts'/f'{task}.txt')==r['context_sha256']
        for arm in ('rag','no_rag'):
            expected=[{'role':'system','content':system},{'role':'user','content':query+(context if arm=='rag' else '')}]
            assert read(P/'messages'/f'{task}__{arm}.json')==expected
            expected_messages[(task,arm)]=expected
        retrieval_results.append({'task':task,'selected_ids':top,'category':row['category']})
    main_tasks={r['id'] for r in risk['rows'] if r['category']=='MAIN_CANDIDATE'}
    main_manifest=P/'console-package-main36.json'
    manifests=[P/'console-package.json']
    if main_manifest.exists():manifests.append(main_manifest)
    reports=[]
    sys.path.insert(0,str(ROOT));from console_bridge_v3 import Package,simulation_verdict
    for row in prior['reference_outcomes']:
        rawlog=read(P/'calibration'/row['task']/'simulate.json')
        verdict=simulation_verdict(rawlog['stdout'],rawlog['returncode'],row['checks'])
        assert verdict=={'fixed_test':'FIXED_TEST_PASS','mismatches':0,'samples':row['checks']}
    for path in manifests:
        package=read(path);slots=package['slots'];groups=defaultdict(list)
        for name,h in package['files'].items():assert sha(P/name)==h,name
        for name,h in read(P/'v3-source-lock.json').items():assert sha(ROOT/name)==h,name
        assert package['purpose']=='DRAFT_REVIEW' and package['budget_policy']=='calls_only'
        assert package['automatic_retries']==0 and package['release_created'] is False
        profiles={m['id']:m for m in package['models']}
        for slot in slots:
            obj=read(P/slot['request']);profile=profiles[slot['model']]
            assert obj['model']==slot['model']
            assert set(obj)=={'model','messages','provider','stream'}|set(profile['parameters'])
            assert obj['messages']==expected_messages[(slot['task'],slot['condition'])]
            assert {k:obj[k] for k in profile['parameters']}==profile['parameters']
            assert obj['provider']=={'only':['openai'],'allow_fallbacks':False,'require_parameters':True}
            assert obj['stream'] is False and not any(k in obj for k in ('max_tokens','max_completion_tokens','tools','seed','temperature'))
            assert slot['expected_checks']==next(x['checks'] for x in prior['reference_outcomes'] if x['task']==slot['task'])
            assert slot['status']=='NOT_STARTED' and slot['reserved'] is False and not slot['assets']
            groups[(slot['task'],slot['condition'])].append((slot['model'],slot['sample']))
            assert next(x['category'] for x in risk['rows'] if x['id']==slot['task'])!='DO_NOT_EXECUTE'
        expected_pairs={(model,sample) for model in profiles for sample in (1,2)}
        assert all(len(x)==6 and set(x)==expected_pairs for x in groups.values())
        imported=Package(path,state=HERE/'NO_EXECUTION_STATE')
        assert len(imported.rows())==len(slots) and not imported.state.exists()
        missing=HERE/'NO_RELEASE_IS_CREATED.json'
        assert not missing.exists()
        try:imported.gate(missing,slots[0]['id']);raise AssertionError('Unexpected release')
        except FileNotFoundError:pass
        if path==main_manifest:
            assert len(slots)==36 and {s['task'] for s in slots}==main_tasks
            full={s['id']:s for s in read(manifests[0])['slots']}
            assert all({k:v for k,v in s.items() if k!='ordinal'}=={k:v for k,v in full[s['id']].items() if k!='ordinal'} for s in slots)
        reports.append({'manifest':path.name,'sha256':sha(path),'slots':len(slots),'message_groups':len(groups),'data_only_console_import':True,'missing_release_blocks':True,'state_created':False})
    out={'status':'PASS','categories':dict(categories),'retrievals':retrieval_results,'messages_checked':60,'v3_parser_saved_logs_passed':30,'packages':reports,'main36_available':main_manifest.exists(),'model_calls':0,'network_calls':0,'eda_calls':0,'limits':['No independent-source oracle; reference self-match is infrastructure calibration','Only messages/context equal across models; Luna reasoning medium vs other model defaults differs, not equal compute','Endpoint snapshots are historical metadata, current inference access unverified','Small main set and two stochastic samples are exploratory only']}
    (HERE/'package-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='retrievals'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
