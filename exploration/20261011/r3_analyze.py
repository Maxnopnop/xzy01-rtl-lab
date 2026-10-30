"""Read-only final R3 evidence audit; outputs outside frozen source/run."""
import sys,json,re
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent;BASE=HERE/'r3';ROOT=HERE.parents[1];sys.path[:0]=[str(BASE),str(ROOT)]
import runner,batch,rtl_lab as lab

def main():
    run=runner.RUN;plan=runner.verify();lock=batch.read(run/'evidence-lock.json');results=batch.read(HERE/'r3-corrected-results.json');summary=batch.read(HERE/'r3-summary.json')
    original=batch.read(run/'results.json');fix=batch.read(HERE/'r3-finalization.json')
    assert lab.digest((run/'results.json').read_bytes())==fix['raw_results_sha256']
    assert lab.digest((HERE/'r3-corrected-results.json').read_bytes())==fix['corrected_results_sha256']
    assert lab.digest((HERE/'r3-summary.json').read_bytes())==fix['summary_sha256']
    for raw,row,job in zip(original,results,plan['jobs']):
        assert row==dict(raw,judge_stage=raw['stage'],stage=job['stage'])
    assert set(lock)=={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')}
    for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,rel
    generated=0;receipts=0;compiles=0;firsts=[];public_statuses=Counter();infra=[]
    def check_sim(folder,result):
        nonlocal receipts,compiles
        cfile=folder/'compile.json'
        if not cfile.exists():assert result['status'] in ('RTL_REJECTED','EXTRACTION_ERROR');return
        c=batch.read(cfile);compiles+=1;assert not c['timeout'] and not c['output_limit']
        if result['status']=='COMPILE_FAIL':assert c['returncode']!=0;return
        assert c['returncode']==0
        if result['status'] not in ('PASS','FUNCTION_FAIL'):return
        sim=batch.read(folder/'simulate.json');assert sim['returncode']==0 and not sim['timeout'] and not sim['output_limit']
        m=re.fullmatch(r'RTL_LAB_V1 ([a-f0-9]+) checks=(\d+) errors=(\d+)',(folder/'verdict.txt').read_text().strip())
        assert m and m[1]==result['receipt_nonce'] and int(m[2])==result['checks']
        assert (int(m[3])==0)==(result['status']=='PASS');receipts+=1
        for name,key in [('dut.sv','rtl_sha256'),('testbench.sv','tb_sha256'),('vectors.hex','vectors_sha256')]:assert lab.digest((folder/name).read_bytes())==result[key]
    def bind_vectors(folder,task,split):
        spec=batch.read(runner.ASSETS/(task+'.json'));rows=batch.read(runner.ASSETS/(task+'-'+split+'.json'))
        iw=sum(w for n,w in spec['inputs']);ow=sum(w for n,w in spec['outputs'])
        words=[int(x,16) for x in (folder/'vectors.hex').read_text().splitlines()]
        assert len(words)==len(rows)
        for word,event in zip(words,rows):
            assert word&((1<<ow)-1)==event['expected']
            packed=word>>ow;assert packed&((1<<iw)-1)==event['input']
            control=packed>>iw;assert control&1==event['rst_n'] and control>>1==event['clk']
    for job,row in zip(plan['jobs'],results):
        assert row['id']==job['id'];folder=run/'jobs'/job['id']
        if row['status']=='PENDING':assert not (folder/'started.json').exists()
        else:
            assert batch.read(folder/'started.json')['reserved_calls']==1
            gen=batch.read(folder/'generation.json')
            if gen['status']=='GENERATED':
                generated+=1;raw=(folder/'response.txt').read_bytes();assert lab.digest(raw)==gen['response_sha256']
                prompt=(folder/'call/exact-prompt.txt').read_text(encoding='utf-8');assert lab.digest(prompt.encode())==gen['prompt_sha256']
                if job['stage']=='first':assert prompt==job['prompt']
                else:
                    parent=run/'jobs'/job['depends_on'];candidate=(parent/'response.txt').read_text(encoding='utf-8');feedback=batch.read(parent/'public-feedback.json') if job['arm']=='feedback' else None
                    assert prompt==runner.branch_prompt(job['task'],candidate,feedback)
                request=batch.read(folder/'call/codex_request.json');assert request['prompt']==prompt and request['requested_model']==plan['model']
                assert request['adapter_sha256']==plan['source_hashes']['codex_network_adapter.py']
                events=[json.loads(x) for x in (folder/'call/codex.stdout.log').read_text(encoding='utf-8').splitlines() if x.strip()]
                completed=[e for e in events if e.get('type')=='turn.completed'];assert completed[-1]['usage']==gen['usage']
                assert not any(e.get('type') in ('error','turn.failed') for e in events)
                itemtypes={e.get('item',{}).get('type') for e in events if e.get('type','').startswith('item.')};assert itemtypes<={'agent_message','reasoning'}
                check_sim(folder/'hidden-check',batch.read(folder/'hidden-judge.json'))
                if (folder/'hidden-check/vectors.hex').exists():bind_vectors(folder/'hidden-check',job['task'],'private')
                assert (folder/'hidden-check/dut.sv').read_bytes()==lab.extract_rtl(raw.decode(),runner.tasks.TASKS[job['task']]['module']).encode()
            else:infra.append(dict(id=job['id'],status=gen['status']))
        if job['stage']=='first':
            publicfile=folder/'public-feedback.json';public=batch.read(publicfile)['status'] if publicfile.exists() else 'NOT_RUN'
            if publicfile.exists():
                # public_feedback is deliberately small; reconstruct simulator bindings for independent receipt check.
                cf=folder/'public-check'
                if (cf/'verdict.txt').exists():
                    m=re.fullmatch(r'RTL_LAB_V1 ([a-f0-9]+) checks=(\d+) errors=(\d+)',(cf/'verdict.txt').read_text().strip());assert m
                    public_rows=batch.read(runner.ASSETS/(job['task']+'-public.json'))
                    check_sim(cf,dict(status=public,checks=len(public_rows),receipt_nonce=m[1],rtl_sha256=lab.digest((cf/'dut.sv').read_bytes()),tb_sha256=lab.digest((cf/'testbench.sv').read_bytes()),vectors_sha256=lab.digest((cf/'vectors.hex').read_bytes())))
                    bind_vectors(cf,job['task'],'public')
                elif (cf/'compile.json').exists():check_sim(cf,dict(status=public))
                else:assert public in ('RTL_REJECTED','EXTRACTION_ERROR')
            classification={'PASS':'CORRECT_ON_FIXED_HIDDEN','FUNCTION_FAIL':'NATURAL_FUNCTIONAL_ERROR','COMPILE_FAIL':'INVALID_COMPILE','RTL_REJECTED':'INVALID_RTL','EXTRACTION_ERROR':'INVALID_RTL_FORMAT','PENDING':'NOT_STARTED'}.get(row['status'],'INFRASTRUCTURE_OR_UNKNOWN')
            firsts.append(dict(id=job['id'],task=job['task'],hidden_status=row['status'],classification=classification,public_status=public));public_statuses[public]+=1
    assert generated==summary['generated']
    oldfiles=0
    for name in ('compound-v1','delayed-v1','factorial20-v1','formal-v1','r1b-v1','r1b-v2','timed-reset-v1','timed-calibration-v1','timed-calibration-v2','r2-prepared-v1'):
        old=HERE/'runs'/name
        for rel,h in batch.read(old/'evidence-lock.json').items():assert lab.digest((old/rel).read_bytes())==h;oldfiles+=1
        for rel,h in batch.read(old/'plan.json')['source_hashes'].items():assert lab.digest((ROOT/rel).read_bytes())==h
    output=dict(status='PASS',checked_utc=lab.utc(),plan_sha256=batch.read(run/'plan-lock.json')['sha256'],dispatch=batch.read(run/'dispatch.json'),planned=24,started=summary['started'],generated=generated,
                fixed_hidden_statuses=summary['statuses'],first_candidates=firsts,first_classifications=dict(Counter(f['classification'] for f in firsts)),first_public_statuses=dict(public_statuses),
                comparisons=summary['comparisons'],effects=summary['effects'],families=summary['families'],actual_unique_usage=summary['actual_unique_usage'],shared_first_usage=summary['shared_first_usage'],arms=summary['arms'],
                actual_generation_seconds=sum(r.get('generation',{}).get('generation_seconds',0) for r in results),actual_adapter_seconds=sum(r.get('generation',{}).get('elapsed_seconds',0) for r in results),
                campaign_through_scoring_wall_seconds=(run/'results.json').stat().st_mtime-batch.read(run/'campaign-start.json')['epoch'],run_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),
                verified_files=len(lock),compile_checks=compiles,simulator_receipts=receipts,old_evidence_files=oldfiles,infrastructure_failures=infra,cost='UNKNOWN',yosys='NOT_RUN',
                scope_correction='Arbiter references have the same reachable state encoding; calibration supports equivalent implementation style only.',
                limits='4 new development families, 8 pairs. Shared first RTL, not IR/table benefit or strict token/compute matching; no output-length filtering.')
    batch.atomic(HERE/'r3-analysis.json',output);print(json.dumps({k:v for k,v in output.items() if k not in ('comparisons','families','first_candidates')},indent=2))
if __name__=='__main__':main()
