"""Bounded 2x2 fixed-compound-IR repair study, using existing guarded adapter."""
import json,sys,time,copy
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import batch,rtl_lab as lab,paired_bank as bank,paired_study as ps,mutation_study as ms,codex_adapter,fsm_study

def init(run):
    cases=batch.read(HERE/'runs/compound-v1/cases.json');profiles=batch.read(ROOT/'evidence/mutation-v1/contracts-v2.json')
    specs=ms.development_specs();chosen={s['id']:next(r for r in cases if r['task']==s['id'] and r['is_fault']) for s in specs}
    jobs=[]
    for i,s in enumerate(specs):
        arms=[('v1','control'),('v1','feedback'),('v2','control'),('v2','feedback')]
        arms=arms[i%4:]+arms[:i%4]
        for profile,arm in arms:
            spec=copy.deepcopy(s)
            if profile=='v2':spec['public_contract']=profiles[s['id']]['contract']
            raw=ms.raw(chosen[s['id']]['ir'])
            jobs.append(dict(id=s['id']+'__'+profile+'__'+arm,task=s['id'],profile=profile,arm=arm,spec=spec,ir=raw,prompt=ps.prompt(spec,raw,arm),case_id=chosen[s['id']]['id']))
    run.mkdir(parents=True)
    plan=dict(kind='DEVELOPMENT_FIXED_COMPOUND_IR_FACTORIAL_V1',created_utc=lab.utc(),model='gpt-5.6-sol',max_calls=20,workers=2,api_timeout=180,reasoning='low',retries=0,jobs=jobs,seed=None,selection='First semantic compound fault per family in frozen enumeration order; no model-based selection',source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in [Path(__file__),HERE/'PROTOCOL.md',HERE/'runs/compound-v1/cases.json',ROOT/'codex_adapter.py',ROOT/'paired_study.py',ROOT/'rtl_lab.py',ROOT/'backends.py',ROOT/'fsm_ir.py',ROOT/'fsm_checks.py',ROOT/'paired_bank.py',ROOT/'evidence/mutation-v1/contracts-v2.json',bank.ROOT/'bank-lock.json']})
    batch.atomic(run/'plan.json',plan);batch.atomic(run/'plan-lock.json',dict(sha256=lab.digest((run/'plan.json').read_bytes())))
    args=SimpleNamespace(iverilog=None,vvp=None)
    batch.atomic(run/'environment.json',lab.inspect_tools(args,run))
    return plan

def generate(run,job,plan):
    folder=run/'jobs'/job['id'];folder.mkdir(parents=True,exist_ok=True)
    if (folder/'generation.json').exists():return batch.read(folder/'generation.json')
    if (folder/'started.json').exists():
        row=dict(status='UNKNOWN_INTERRUPTED',usage=None);batch.atomic(folder/'generation.json',row);return row
    batch.atomic(folder/'started.json',dict(utc=lab.utc(),reserved_calls=1,model=plan['model']))
    call=folder/'call';call.mkdir()
    args=SimpleNamespace(codex_executable=None,model=plan['model'],codex_reasoning=plan['reasoning'],api_timeout=plan['api_timeout'])
    start=time.monotonic()
    try:
        output,meta=codex_adapter.generate_text(args,call,job['prompt'])
        lab.write_text(folder/'response.txt',output)
        row=dict(status='GENERATED',response_sha256=lab.digest((folder/'response.txt').read_bytes()),**meta)
    except lab.LabError as exc:row=dict(status=exc.status,stage=exc.stage,message=exc.message,usage=None)
    except Exception as exc:row=dict(status='ENV_ERROR',message=str(exc),usage=None)
    row['elapsed_seconds']=time.monotonic()-start;batch.atomic(folder/'generation.json',row)
    print(job['id'],row['status'],round(row['elapsed_seconds'],2),flush=True)
    return row

def main():
    run=HERE/'runs/factorial20-v1';plan=init(run) if not run.exists() else batch.read(run/'plan.json')
    assert lab.digest((run/'plan.json').read_bytes())==batch.read(run/'plan-lock.json')['sha256']
    for p,h in plan['source_hashes'].items():assert lab.digest((ROOT/p).read_bytes())==h,p
    jobs=plan['jobs'];start=time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=list(pool.map(lambda j:generate(run,j,plan),jobs[:4]))
        gate=all(r['status']=='GENERATED' for r in first)
        batch.atomic(run/'gate.json',dict(first4_completed=gate,rule='Service reliability only, not functional results'))
        if gate:
            # Stop after any infrastructure failure in each remaining four-call batch.
            for k in range(4,20,4):
                rows=list(pool.map(lambda j:generate(run,j,plan),jobs[k:k+4]))
                if any(r['status']!='GENERATED' for r in rows):break
    # Hidden scoring begins only after all generation dispatched for this phase.
    args=SimpleNamespace(compile_timeout=15,sim_timeout=10);tools=batch.read(run/'environment.json')
    results=[];usage=Counter();status=Counter();started=0
    for job in jobs:
        folder=run/'jobs'/job['id'];row={k:job[k] for k in ('id','task','profile','arm','case_id')}
        if (folder/'started.json').exists():started+=1
        if not (folder/'generation.json').exists():row.update(status='PENDING',usage=None)
        else:
            gen=batch.read(folder/'generation.json');row['generation']=gen
            if gen['status']=='GENERATED':
                if (folder/'result.json').exists():row=batch.read(folder/'result.json')
                else:row.update(ps.judge(folder,job['spec'],(folder/'response.txt').read_text(encoding='utf-8'),job['ir'],tools,args))
                for key,value in (gen.get('usage') or {}).items():
                    if isinstance(value,(int,float)):usage[key]+=value
            else:row.update(status=gen['status'],usage=None)
        status[row['status']]+=1;results.append(row)
        if folder.exists():batch.atomic(folder/'result.json',row)
    comparisons=[]
    for task in dict.fromkeys(j['task'] for j in jobs):
        for profile in ('v1','v2'):
            a=next(r for r in results if r['task']==task and r['profile']==profile and r['arm']=='control')['status']
            b=next(r for r in results if r['task']==task and r['profile']==profile and r['arm']=='feedback')['status']
            effect='INCONCLUSIVE' if a not in ('PASS','FUNCTION_FAIL','COMPILE_FAIL') or b not in ('PASS','FUNCTION_FAIL','COMPILE_FAIL') else ('help' if a!='PASS' and b=='PASS' else 'harm' if a=='PASS' and b!='PASS' else 'no_change')
            comparisons.append(dict(task=task,profile=profile,control=a,feedback=b,effect=effect))
    batch.atomic(run/'summary.json',dict(kind=plan['kind'],planned=20,started=started,generated=sum('generation' in r and r['generation']['status']=='GENERATED' for r in results),statuses=dict(status),usage=dict(usage),cost='UNKNOWN; existing account usage, no reported billing',elapsed_this_invocation=time.monotonic()-start,results=results,comparisons=comparisons,limits='Five development families, one output/cell, injected IR conditional repair; not end-to-end, not equal compute, not final-set generalization. No resampling.'))
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})
if __name__=='__main__':main()
