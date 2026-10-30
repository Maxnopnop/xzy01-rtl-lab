"""Offline fixtures and mock control-flow tests; never call network adapter."""
import sys,json,copy
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import r2,batch,rtl_lab as lab,paired_bank as bank,paired_study as ps,fsm_ir,r1b_v2
def main():
    run=HERE/'runs/r2-offline-v1';assert not run.exists();run.mkdir()
    with patch.object(bank,'oracle',side_effect=AssertionError('Private oracle access forbidden')),patch.object(fsm_ir,'product_check',side_effect=AssertionError('Private equivalence access forbidden')),patch.object(r2.adapter,'generate_text',side_effect=AssertionError('Network forbidden')):
        plan=r2.prepare(run/'fixture-plan');r2.verify(run/'fixture-plan')
        pairs={}
        for j in plan['jobs']:pairs.setdefault(j['pair'],[]).append(j)
        assert len(pairs)==10
        for pair,js in pairs.items():
            assert len(js)==2 and js[0]['common_sha256']==js[1]['common_sha256'] and js[0]['candidate_sha256']==js[1]['candidate_sha256'] and js[0]['spec']==js[1]['spec']
            control=next(j for j in js if j['arm']=='regeneration');fb=next(j for j in js if j['arm']=='feedback')
            from fsm_study import NO_TOOLS
            prefix=control['prompt'][:-len('\n'+NO_TOOLS)]
            expected=prefix+'\nExecutable results on the already-public contract:\n'+json.dumps(bank.feedback(fb['ir'],fb['spec']['public_contract']),indent=2)+'\n'+'\n'+NO_TOOLS
            assert fb['prompt']==expected
    calls=[]
    def ok(args,folder,prompt):calls.append(folder);return 'mock response',dict(tools_used=False,usage=dict(output_tokens=1))
    full=run/'mock-complete';full.mkdir();out=r2.campaign(full,plan,ok);assert len(calls)==20 and out['gate'] and out['status']=='GENERATION_COMPLETE'
    r2.campaign(full,plan,ok);assert len(calls)==20
    failed=run/'mock-api-error';failed.mkdir();count=0
    def fail(args,folder,prompt):
        nonlocal count
        count+=1;raise lab.LabError('API_ERROR','mock','Synthetic HTTP403; no actual request')
    out=r2.campaign(failed,plan,fail);assert count==1 and not out['gate']
    r2.campaign(failed,plan,ok);assert count==1 and len(calls)==20
    unknown=run/'mock-unknown';folder=unknown/'jobs'/plan['jobs'][0]['id'];folder.mkdir(parents=True);batch.atomic(folder/'started.json',dict(reserved_calls=1))
    out=r2.campaign(unknown,plan,ok);assert out['status']=='STOPPED_INFRASTRUCTURE' and len(calls)==20
    gate=run/'mock-after-gate';gate.mkdir();gatecalls=0
    def fifthfail(args,folder,prompt):
        nonlocal gatecalls
        gatecalls+=1
        if gatecalls==5:raise lab.LabError('API_ERROR','mock','Synthetic service failure')
        return ok(args,folder,prompt)
    out=r2.campaign(gate,plan,fifthfail);assert gatecalls==5 and out['gate'] and out['status']=='STOPPED_INFRASTRUCTURE'
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10);tools=lab.inspect_tools(args,run);judges=[]
    for task in r2.TASKS:
        job=next(j for j in plan['jobs'] if j['task']==task);folder=run/'fixture-judge'/task;folder.mkdir(parents=True)
        text=r1b_v2.reference(task,job['spec']['module'],job['spec']['ports']);row=ps.judge(folder,job['spec'],text,job['ir'],tools,args)
        assert row['status']==row['spec_diagnostic']['status']=='PASS' and row['ir_rtl']['status']=='FUNCTION_FAIL' and row['diagnostic_consistent']
        judges.append(dict(task=task,case_kind=job['case']['kind'],**row))
    summary=dict(status='PASS',real_model_calls=0,mock_adapter_invocations=30,icarus_evaluations=15,prompt_pairs=10,
                 checker_boundary='No oracle/product_check during prompt creation',tests=['20-cap','no-repeat-complete','stop-first-API-error','no-retry-API-error','unknown-stops','4-service-gate','stop-fifth-failure'],judges=judges,
                 label='ENGINEERING_OFFLINE_FIXTURES_ONLY; no generation effect estimate')
    # 20 completion +1 first error +5 gate dispatch, only 4 successful gate calls: 26 adapter invocations.
    summary['mock_adapter_invocations']=20+count+gatecalls
    batch.atomic(run/'summary.json',summary);batch.atomic(run/'source-lock.json',{str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in [Path(__file__),HERE/'r2.py',HERE/'R2_PROTOCOL.md']})
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
    print(json.dumps({k:v for k,v in summary.items() if k!='judges'},indent=2))
if __name__=='__main__':main()
