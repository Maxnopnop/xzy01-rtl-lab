"""Read-only completed-batch audit. No model, judge or simulator dispatch."""
import importlib.util,json,sys
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parent;BASE=OUT.parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE));sys.path.insert(1,str(ROOT))
import stream_process as sp,intent,tasks,prompts

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def check_bindings(lock,base):
    d=sp.read(lock)
    for rel,h in d.items():
        f=Path(rel) if Path(rel).is_absolute() else base/rel
        assert f.is_file() and sp.digest(f.read_bytes())==h,str(f)
    return len(d)

def analyze():
    candidate=load('r6_actual_candidate',BASE/'engineering-v2/runner.py');core=candidate.core
    run=core.RUN;p=core.verify();sha=sp.digest((run/'plan.json').read_bytes())
    assert sha==sp.read(OUT/'release.json')['plan_sha256']
    assert (run/'evidence-lock.json').exists(),'Wait for original batch seal; never close active run'
    nseal=check_bindings(run/'evidence-lock.json',run)
    actual={str(x.relative_to(run)) for x in run.rglob('*') if x.is_file() and x.name not in ['evidence-lock.json','run.lock']}
    assert actual==set(sp.read(run/'evidence-lock.json'))
    prep=check_bindings(BASE/'packet-lock.json',BASE);prior=check_bindings(BASE/'prior-lock.json',ROOT)
    results=sp.read(run/'results.json');byid={r['id']:r for r in results};assert set(byid)=={j['id'] for j in p['jobs']}
    cli=[];reserved=[];pending=[];unknown=[];input_limit=[];judges=[];observations=[]
    def raw(jid):
        folder=run/'jobs'/jid;g=sp.read(folder/'generation.json');b=(folder/'response.txt').read_bytes()
        assert sp.digest(b)==g['response_sha256'];return b.decode('utf-8')
    for j in p['jobs']:
        f=run/'jobs'/j['id'];row=byid[j['id']];assert row['role']==j['role'] and row['arm']==j['arm'] and row['representation']==j['representation']
        if (f/'started.json').exists():reserved.append(j['id'])
        gf=f/'generation.json'
        if not gf.exists():
            assert row['status']=='PENDING';pending.append(j['id']);continue
        g=sp.read(gf);assert row['generation']==g
        if g['status']!='GENERATED':
            if g['status']=='INPUT_LIMIT':input_limit.append(j['id']);assert not g['model_called']
            else:unknown.append(dict(id=j['id'],status=g['status'],usage=g.get('usage'),stage=g.get('stage'),message=g.get('message')))
            assert row['status']==g['status'];continue
        r=sp.recover(f/'call');assert r['status']=='GENERATED',(j['id'],r)
        req=sp.read(f/'call/request.json');proof=sp.read(f/'call/exit-proof.json')
        assert req['model']==p['model'] and req['context']['reasoning']==p['reasoning']
        assert req['timeout']==p['api_timeout'] and req['output_limit']==p['output_byte_limit']
        assert req['context']['adapter_sha256']==sp.digest((BASE/'cli_adapter.py').read_bytes()) and req['context']['process_sha256']==sp.digest((BASE/'stream_process.py').read_bytes())
        actual_prompt=(f/'call/exact-prompt.txt').read_bytes()
        assert actual_prompt==(f/'call/prompt.bin').read_bytes()
        assert sp.digest(actual_prompt)==g['prompt_sha256']==req['prompt_sha256'] and len(actual_prompt)==g['prompt_bytes']
        if 'prompt' in j:expected=j['prompt']
        elif j['role']=='first_rtl':expected=prompts.first(j['task'],'structured',raw(j['intent_id']))
        elif j['role']=='direct_second':expected=prompts.second(j['task'],raw(j['first_id']))
        else:
            fb=sp.read(run/'jobs'/j['first_id']/'public-feedback.json') if j['arm']=='feedback' else None
            expected=prompts.branch(j['task'],j['representation'],None,raw(j['first_id']),fb)
        assert actual_prompt==expected.encode(),j['id']+' parent/template mismatch'
        assert r['response']==raw(j['id']) and r['usage']==g['usage'] and r['thread_id']==g['codex_thread_id']
        assert (f/'call/model_output.raw.txt').read_bytes()==r['response'].encode()
        cli.append(dict(id=j['id'],thread_id=r['thread_id'],role=j['role'],representation=j['representation'],arm=j['arm'],usage=g['usage'],
                        event_sha256=sp.digest((f/'call/stdout.bin').read_bytes()),stderr_sha256=sp.digest((f/'call/stderr.bin').read_bytes()),exit_sha256=sp.digest((f/'call/exit-proof.json').read_bytes()),
                        request_sha256=sp.digest((f/'call/request.json').read_bytes()),prompt_sha256=g['prompt_sha256'],response_sha256=g['response_sha256'],
                        prompt_bytes=g['prompt_bytes'],version=req['context']['cli_version'],exe_sha256=req['context']['executable_sha256'],
                        cli_seconds=proof['elapsed_seconds'],adapter_seconds=g['elapsed_seconds'],returncode=proof['returncode']))
        checks=row['judge'];assert checks==sp.read(f/'hidden-judge.json')
        if j['role']=='intent':
            ir,_=intent.check(raw(j['id']),'structured',j['task'],sp.read(BASE/'assets'/(j['task']+'-private.json')))
            assert ir==checks['intent_spec'];assert row['status']==ir['status']
        else:
            assert row['status']==checks['rtl_spec']['status']
            if j['representation']=='structured':
                ir,values=intent.check(raw(j['intent_id']),'structured',j['task'],sp.read(BASE/'assets'/(j['task']+'-private.json')))
                assert checks['intent_spec']==ir
                a,b,c=[checks[k]['status'] for k in ['intent_spec','rtl_spec','rtl_intent']]
                observations.append(dict(id=j['id'],intent_spec=a,rtl_spec=b,rtl_intent=c,category=core.classify(a,b,c)))
    assert len({c['thread_id'] for c in cli})==len(cli)
    assert len(reserved)<=48 and len(cli)+len(unknown)+len(pending)+len(input_limit)==48
    # Actual EDA receipts and vector domains, including the genuine model IR path.
    for j in p['jobs']:
        f=run/'jobs'/j['id']
        for folder in [f/'public',f/'hidden-spec',f/'hidden-intent']:
            if not (folder/'compile.json').exists():continue
            comp=sp.read(folder/'compile.json');sim=sp.read(folder/'simulate.json') if (folder/'simulate.json').exists() else None
            rows=sp.read(BASE/'assets'/(j['task']+('-public.json' if folder.name=='public' else '-private.json')))
            if folder.name=='hidden-intent':
                _,v=intent.check(raw(j['intent_id']),'structured',j['task'],rows);assert v is not None
                rows=[dict(r,expected=x) for r,x in zip(rows,v)]
            iw=sum(w for n,w in tasks.TASKS[j['task']]['inputs']);ow=sum(w for n,w in tasks.TASKS[j['task']]['outputs'])
            words=(folder/'vectors.hex').read_text().splitlines();assert len(words)==len(rows)
            for word,row in zip(words,rows):
                value=int(word,16);assert value&((1<<ow)-1)==row['expected'];value>>=ow
                assert value&((1<<iw)-1)==row['input'];value>>=iw
                assert value&1==row['rst_n'] and value>>1==row['clk']
            receipt=None
            if folder.name=='public':
                # Public compact feedback omits hashes; source files remain bound by seal.
                receipt=sp.read(f/'public-feedback.json')
            else:receipt=byid[j['id']]['judge']['rtl_spec' if folder.name=='hidden-spec' else 'rtl_intent']
            for filename,key in [('dut.sv','rtl_sha256'),('testbench.sv','tb_sha256'),('vectors.hex','vectors_sha256')]:
                if key in receipt:assert sp.digest((folder/filename).read_bytes())==receipt[key]
            nonce=None;errors=None
            if sim and sim['returncode']==0 and (folder/'verdict.txt').exists():
                tokens=(folder/'verdict.txt').read_text().strip().split();assert tokens[0]=='RTL_LAB_V1'
                nonce=tokens[1];assert '+nonce='+nonce in sim['command']
                assert int(tokens[2].split('=')[1])==len(rows);errors=int(tokens[3].split('=')[1])
                if 'receipt_nonce' in receipt:assert receipt['receipt_nonce']==nonce
                if receipt['status']=='PASS':assert errors==0
                if receipt['status']=='FUNCTION_FAIL':assert errors>0
            judges.append(dict(id=j['id'],kind=folder.name,folder=str(folder.relative_to(BASE)),status=receipt['status'],
                               compile_returncode=comp['returncode'],simulate_returncode=sim['returncode'] if sim else None,checks=len(rows),nonce=nonce,errors=errors,
                               compile_timeout=comp['timeout'],simulate_timeout=sim['timeout'] if sim else None))
    nonces=[j['nonce'] for j in judges if j['nonce']];assert len(set(nonces))==len(nonces)
    summary=sp.read(run/'summary.json');assert summary==core.summarize(results,p)
    assert summary['observations']==observations
    keys=['input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens']
    known={k:sum(c['usage'][k] for c in cli if isinstance(c['usage'].get(k),(int,float))) for k in keys}
    missing={k:sum(not isinstance(c['usage'].get(k),(int,float)) for c in cli) for k in keys}
    ledger={}
    for rep in ['structured','direct']:
        shared=[c for c in cli if c['representation']==rep and c['arm']=='shared']
        shared_reserved=sum(byid[jid]['representation']==rep and byid[jid]['arm']=='shared' for jid in reserved)
        for arm in ['regeneration','feedback']:
            branch=[c for c in cli if c['representation']==rep and c['arm']==arm]
            branch_reserved=sum(byid[jid]['representation']==rep and byid[jid]['arm']==arm for jid in reserved)
            ledger[rep+'_'+arm]=dict(planned_denominator=6,planned_opportunities=18,planned_half_shared_calls=12,
                reserved_half=shared_reserved/2+branch_reserved,known_completed_half=len(shared)/2+len(branch),
                known_half_usage={k:sum(c['usage'].get(k,0) for c in shared if isinstance(c['usage'].get(k),(int,float)))/2+
                                    sum(c['usage'].get(k,0) for c in branch if isinstance(c['usage'].get(k),(int,float))) for k in keys},
                missing_provider_fields={k:sum(not isinstance(c['usage'].get(k),(int,float)) for c in shared+branch) for k in keys},
                strategy=summary['strategies'][rep+'_'+arm])
    assert {k:sum(v['known_half_usage'][k] for v in ledger.values()) for k in keys}==known
    assert sum(v['reserved_half'] for v in ledger.values())==len(reserved)
    family={t:dict(Counter(r['status'] for r in results if r['task']==t)) for t in tasks.TASKS}
    status='COMPLETE' if not pending and not unknown and not input_limit else 'STOPPED_OR_PARTIAL'
    gate=sp.read(OUT/'service-gate-audit.json') if (OUT/'service-gate-audit.json').exists() else None
    if gate:assert [x['id'] for x in gate['first_four']]==[j['id'] for j in p['jobs'][:4]]
    return dict(audit_status='PASS',batch_state=status,dispatch=sp.read(run/'dispatch.json'),plan_sha256=sha,
                source_bindings=len(p['source_hashes']),preparation_bindings_preserved=prep,prior_bindings_preserved=prior,run_seal_files=nseal,
                planned_unique_calls=48,reserved_calls=len(reserved),clean_completed_calls=len(cli),unknown_reservations=unknown,
                pending=pending,input_limit_no_dispatch=input_limit,service_gate='PASS' if gate else 'NOT_PASSED',known_completed_usage=known,
                missing_known_provider_fields=missing,total_provider_usage=known if not unknown and not any(missing.values()) else None,
                fees='UNKNOWN',cache_reasoning_note='Cached input is inside input; reasoning inside output; do not add twice',
                cli_seconds=sum(c['cli_seconds'] for c in cli),adapter_seconds=sum(c['adapter_seconds'] for c in cli),
                versions=dict(Counter(c['version'] for c in cli)),exe_hashes=dict(Counter(c['exe_sha256'] for c in cli)),
                prompt_byte_range=[min(c['prompt_bytes'] for c in cli),max(c['prompt_bytes'] for c in cli)] if cli else None,
                compile_calls=len(judges),simulate_calls=sum(j['simulate_returncode'] is not None for j in judges),
                simulated_event_checks=sum(j['checks'] for j in judges if j['nonce'] is not None),
                role_statuses=summary['role_statuses'],summary=summary,by_family=family,ledger=ledger,observations=observations,cli=cli,judge_receipts=judges,
                no_replay='Auditor has 0 model/simulator/judge calls; raw original outputs only',scope='Same-author small binary #2 development pilot, not final set/unbounded/PPA/strict-token-fairness')
if __name__=='__main__':
    output=OUT/'actual-analysis.json'
    data=analyze()
    if '--verify' not in sys.argv:
        assert not output.exists(),'Never overwrite audit output'
        sp.atomic(output,data)
    print(json.dumps({k:data[k] for k in ['audit_status','batch_state','reserved_calls','clean_completed_calls','compile_calls','simulate_calls','known_completed_usage','plan_sha256']}))
