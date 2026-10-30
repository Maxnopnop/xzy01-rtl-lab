"""Post-process R3 role collision; no model or simulator calls."""
import sys,json
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent;BASE=HERE/'r3';ROOT=HERE.parents[1];sys.path[:0]=[str(BASE),str(ROOT)]
import runner,batch,rtl_lab as lab

def main():
    run=runner.RUN;plan=runner.verify();raw=batch.read(run/'results.json');rows=[]
    assert len(raw)==len(plan['jobs'])==24 and not (run/'evidence-lock.json').exists()
    assert batch.read(run/'dispatch.json')['status']=='GENERATION_COMPLETE'
    for job,row in zip(plan['jobs'],raw):
        assert row['id']==job['id']
        folder=run/'jobs'/job['id'];gen=batch.read(folder/'generation.json');judge=batch.read(folder/'hidden-judge.json')
        assert gen['status']=='GENERATED' and judge['status']==row['status']
        assert lab.digest((folder/'response.txt').read_bytes())==gen['response_sha256']
        corrected=dict(row,judge_stage=row['stage'],stage=job['stage']);rows.append(corrected)
    comparisons=[]
    for pair in plan['pairs']:
        arms={r['arm']:r for r in rows if r['pair']==pair['id'] and r['stage']=='branch'}
        a=arms['regeneration']['status'];b=arms['feedback']['status'];valid={'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED','EXTRACTION_ERROR'}
        effect='inconclusive' if a not in valid or b not in valid else 'help' if a!='PASS' and b=='PASS' else 'harm' if a=='PASS' and b!='PASS' else 'no_change'
        comparisons.append(dict(pair=pair['id'],task=pair['task'],regeneration=a,feedback=b,effect=effect))
    keys=('input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens')
    def usage(group):return {k:sum(r['usage'][k] for r in group) if group and all(isinstance((r.get('usage') or {}).get(k),(int,float)) for r in group) else None for k in keys}
    generated=[r for r in rows if r['generation']['status']=='GENERATED'];first=[r for r in generated if r['stage']=='first'];shared=usage(first);arms={}
    for arm in ('regeneration','feedback'):
        branch=[r for r in generated if r['arm']==arm];us=usage(branch)
        full={k:shared[k]+us[k] if shared[k] is not None and us[k] is not None else None for k in keys}
        split={k:shared[k]/2+us[k] if shared[k] is not None and us[k] is not None else None for k in keys}
        passes=sum(r['status']=='PASS' for r in branch)
        arms[arm]=dict(planned_branch_slots=8,branch_generated=len(branch),branch_statuses=dict(Counter(r['status'] for r in branch)),strategy_call_opportunities=16,
                       shared_first_plus_branch_usage=full,half_shared_allocated_usage=split,branch_usage=us,
                       branch_elapsed_seconds=sum(r['generation']['elapsed_seconds'] for r in branch),
                       shared_plus_branch_elapsed_seconds=sum(r['generation']['elapsed_seconds'] for r in first+branch),
                       pass_per_1000_allocated_output_tokens=passes*1000/split['output_tokens'] if split['output_tokens'] else None)
    summary=dict(planned_unique_calls=24,started=len(list((run/'jobs').glob('*/started.json'))),generated=len(generated),statuses=dict(Counter(r['status'] for r in rows)),
                 first_candidate_statuses=dict(Counter(r['status'] for r in first)),effects=dict(Counter(c['effect'] for c in comparisons)),comparisons=comparisons,families={t:[c for c in comparisons if c['task']==t] for t in runner.tasks.TASKS},
                 actual_unique_usage=usage(generated),shared_first_usage=shared,arms=arms,cost='UNKNOWN',yosys='NOT_RUN',label='Predeclared aggregation recovered from immutable plan roles; raw results unchanged')
    batch.atomic(HERE/'r3-corrected-results.json',rows);batch.atomic(HERE/'r3-summary.json',summary)
    # The original process exited. No run records are replaced; only first evidence seal is added.
    runner.seal(run)
    batch.atomic(HERE/'r3-finalization.json',dict(status='PASS',reason='judge.stage overwrote generation-role stage; original summary KeyError',action='Plan-bound roles and predeclared aggregates outside run, one-time evidence seal',model_calls=0,icarus_evaluations=0,
                 raw_results_sha256=lab.digest((run/'results.json').read_bytes()),corrected_results_sha256=lab.digest((HERE/'r3-corrected-results.json').read_bytes()),summary_sha256=lab.digest((HERE/'r3-summary.json').read_bytes())))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
