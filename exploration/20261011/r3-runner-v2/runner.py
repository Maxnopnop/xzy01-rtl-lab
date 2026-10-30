"""R3 runner v2, separate namespace and invalid-format retention; prepare-only by default; exact released plan hash required for run."""
import sys,json,time,datetime,argparse
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OLD=BASE.parent/"r3";sys.path[:0]=[str(BASE),str(OLD),str(ROOT)]
import tasks,judge,batch,rtl_lab as lab,codex_network_adapter as adapter
from fsm_study import NO_TOOLS
RUN=BASE/'runs/prepared-v2';ASSETS=OLD/'assets-v1'
FUNCTIONAL_STATUSES=frozenset({'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED','EXTRACTION_ERROR'})

def hashes():
    paths=sorted(p for p in BASE.iterdir() if p.is_file() and p.suffix=='.py')+[BASE/'PROTOCOL.md',OLD/'tasks.py']
    paths+=sorted((OLD/'references').glob('*.sv'))+sorted(ASSETS.glob('*.json'))
    paths+=[ROOT/n for n in ('codex_network_adapter.py','codex_adapter.py','rtl_lab.py','backends.py','batch.py','fsm_study.py')]
    return {str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths}

def facts(task):
    spec=batch.read(ASSETS/(task+'.json'));rows=batch.read(ASSETS/(task+'-public.json'))
    interface='input clk, rst_n; '+', '.join(f'input [{w-1}:0] {n}' if w>1 else 'input '+n for n,w in spec['inputs'])+'; '+', '.join(f'output [{w-1}:0] {n}' if w>1 else 'output '+n for n,w in spec['outputs'])
    examples=[[e['clk'],e['rst_n'],e['input'],e['expected']] for e in rows]
    return (lab.SYSTEM_PROMPT+'\nModule: '+spec['module']+'\nInterface: '+interface+'\nSpecification: '+spec['spec']+
            '\nPublic input concatenation, MSB first: '+','.join(n for n,w in spec['inputs'])+
            '\nPublic expected output concatenation, MSB first: '+','.join(n for n,w in spec['outputs'])+
            '\nPublic event examples [clk,rst_n,packed_input,packed_expected_output], check after settling:\n'+json.dumps(examples,separators=(',',':'))+'\n')

def first_prompt(task):return facts(task)+'\nProduce your first RTL implementation candidate. Return only the specified module.\n'+NO_TOOLS

def branch_prompt(task,candidate,feedback=None):
    common=facts(task)+'\nShared first candidate (untrusted; may contain errors):\n'+candidate+'\nImplement the specification. You may correct the candidate while producing RTL. Return only the specified module. No further repair turn.\n'
    return common+('Public execution results:\n'+json.dumps(feedback,separators=(',',':'))+'\n' if feedback is not None else '')+NO_TOOLS

def prepare(run=RUN):
    assert batch.read(OLD/'runs/calibration-v1/summary.json')['status']=='PASS'
    assert batch.read(BASE/'runs/acceptance-v1/summary.json')['status']=='PASS'
    assert not run.exists();run.mkdir(parents=True);pairs=[];jobs=[]
    for repeat in (1,2):
        for i,task in enumerate(tasks.TASKS):
            pair=task+'__r'+str(repeat);first=pair+'__first';pairs.append(dict(id=pair,task=task,repeat=repeat,first=first,arms=['feedback','regeneration'] if (i+repeat)%2 else ['regeneration','feedback']))
            prompt=first_prompt(task);p=run/'prompts'/first;p.mkdir(parents=True);(p/'prompt.txt').write_bytes(prompt.encode())
            jobs.append(dict(id=first,pair=pair,task=task,role='first',arm='shared',prompt=prompt,prompt_sha256=lab.digest(prompt.encode())))
    for pair in pairs:
        for arm in pair['arms']:jobs.append(dict(id=pair['id']+'__'+arm,pair=pair['id'],task=pair['task'],role='branch',arm=arm,depends_on=pair['first']))
    plan=dict(kind='R3_RUNNER_V2_ENGINEERING_PREPARATION',created_utc=lab.utc(),model='gpt-5.6-sol',reasoning='low',api_timeout=180,workers=1,max_calls=24,retries=0,wall_budget_seconds=5400,disk_budget_bytes=500*1024*1024,pairs=pairs,jobs=jobs,source_hashes=hashes(),branch_template='facts + identical raw first candidate + identical implementation instruction; feedback only adds public execution JSON')
    batch.atomic(run/'plan.json',plan);batch.atomic(run/'plan-lock.json',dict(sha256=lab.digest((run/'plan.json').read_bytes())))
    batch.atomic(run/'preparation-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
    return plan

def verify(run=RUN):
    plan=batch.read(run/'plan.json');assert lab.digest((run/'plan.json').read_bytes())==batch.read(run/'plan-lock.json')['sha256']
    assert plan['source_hashes']==hashes(),'Source/asset changed'
    for rel,h in batch.read(run/'preparation-lock.json').items():assert lab.digest((run/rel).read_bytes())==h
    assert len(plan['jobs'])==plan['max_calls']==24 and len(plan['pairs'])==8
    return plan

def generate(run,job,plan,prompt,call=None):
    folder=run/'jobs'/job['id'];folder.mkdir(parents=True,exist_ok=True);g=folder/'generation.json'
    if g.exists():return batch.read(g)
    if (folder/'started.json').exists():row=dict(status='UNKNOWN_INTERRUPTED',usage=None)
    else:
        spent=sum(batch.read(p)['reserved_calls'] for p in (run/'jobs').glob('*/started.json'))
        if spent>=plan['max_calls']:return dict(status='BUDGET_STOP',usage=None)
        batch.atomic(folder/'started.json',dict(reserved_calls=1,utc=lab.utc()));c=folder/'call';c.mkdir();(c/'exact-prompt.txt').write_bytes(prompt.encode());start=time.monotonic()
        args=SimpleNamespace(codex_executable=None,model=plan['model'],codex_reasoning=plan['reasoning'],api_timeout=plan['api_timeout'])
        try:
            raw,meta=(call or adapter.generate_text)(args,c,prompt)
            if meta.get('tools_used') is not False:raise lab.LabError('RTL_REJECTED','tools','Tool use violates generation boundary')
            (folder/'response.txt').write_bytes(raw.encode());row=dict(status='GENERATED',response_sha256=lab.digest(raw.encode()),prompt_sha256=lab.digest(prompt.encode()),**meta)
        except lab.LabError as exc:row=dict(status=exc.status,stage=exc.stage,message=exc.message,usage=None)
        except Exception as exc:row=dict(status='ENV_ERROR',message=str(exc),usage=None)
        row['elapsed_seconds']=time.monotonic()-start
    batch.atomic(g,row);return row

def campaign(run,plan,call=None,public=None,check_sources=True):
    for p in (run/'jobs').glob('*/started.json'):
        g=p.parent/'generation.json'
        if not g.exists():batch.atomic(g,dict(status='UNKNOWN_INTERRUPTED',usage=None))
        if batch.read(g)['status']!='GENERATED':return dict(status='STOPPED_INFRASTRUCTURE',reason='Prior failed/unknown reservation')
    startfile=run/'campaign-start.json'
    if not startfile.exists():batch.atomic(startfile,dict(epoch=time.time()))
    started=batch.read(startfile)['epoch']
    for index,job in enumerate(plan['jobs']):
        if check_sources and plan['source_hashes']!=hashes():return dict(status='SOURCE_CHANGED')
        if time.time()-started>plan['wall_budget_seconds']:return dict(status='BUDGET_STOP',reason='dispatch wall budget')
        if sum(p.stat().st_size for p in run.rglob('*') if p.is_file())>plan['disk_budget_bytes']:return dict(status='BUDGET_STOP',reason='disk budget')
        if job['role']=='first':prompt=job['prompt']
        else:
            parent=run/'jobs'/job['depends_on'];g=batch.read(parent/'generation.json');data=(parent/'response.txt').read_bytes();assert lab.digest(data)==g['response_sha256'];raw=data.decode()
            feedbackfile=parent/'public-feedback.json'
            if not feedbackfile.exists():
                rows=batch.read(ASSETS/(job['task']+'-public.json'))
                feedback=(public or judge.public_feedback)(job['task'],raw,rows,parent/'public-check')
                batch.atomic(feedbackfile,feedback)
            feedback=batch.read(feedbackfile)
            if feedback['status'] not in FUNCTIONAL_STATUSES:return dict(status='STOPPED_INFRASTRUCTURE',reason='Public checker infrastructure')
            prompt=branch_prompt(job['task'],raw,feedback if job['arm']=='feedback' else None)
        row=generate(run,job,plan,prompt,call)
        if row['status']!='GENERATED':return dict(status='STOPPED_INFRASTRUCTURE' if row['status']!='BUDGET_STOP' else 'BUDGET_STOP',reason=row['status'])
        if index==3:batch.atomic(run/'gate.json',dict(passed=True,criterion='4 generation successes only; not functional score'))
    return dict(status='GENERATION_COMPLETE')

def score(run,plan):
    rows=[]
    for job in plan['jobs']:
        folder=run/'jobs'/job['id'];row=dict(job);g=folder/'generation.json'
        row.pop('prompt',None)
        if not g.exists():row.update(status='PENDING',usage=None)
        else:
            gen=batch.read(g);row['generation']=gen;row['usage']=gen.get('usage')
            if gen['status']=='GENERATED':
                data=(folder/'response.txt').read_bytes();assert lab.digest(data)==gen['response_sha256'];jf=folder/'hidden-judge.json'
                if not jf.exists():batch.atomic(jf,judge.simulate(folder/'hidden-check',job['task'],data.decode(),batch.read(ASSETS/(job['task']+'-private.json'))))
                row['judge']=batch.read(jf)
                row['status']=row['judge']['status']
            else:row['status']=gen['status']
        rows.append(row)
    batch.atomic(run/'results.json',rows)
    comparisons=[];valid=FUNCTIONAL_STATUSES
    for pair in plan['pairs']:
        branches={r['arm']:r for r in rows if r['pair']==pair['id'] and r['role']=='branch'}
        a=branches['regeneration']['status'];b=branches['feedback']['status']
        effect='inconclusive' if a not in valid or b not in valid else 'help' if a!='PASS' and b=='PASS' else 'harm' if a=='PASS' and b!='PASS' else 'no_change'
        comparisons.append(dict(pair=pair['id'],task=pair['task'],regeneration=a,feedback=b,effect=effect))
    keys=('input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens')
    def usage(group):return {k:sum(r['usage'][k] for r in group) if group and all(isinstance((r.get('usage') or {}).get(k),(int,float)) for r in group) else None for k in keys}
    generated=[r for r in rows if r.get('generation',{}).get('status')=='GENERATED'];shared=[r for r in generated if r['role']=='first'];shared_usage=usage(shared);arms={}
    for arm in ('regeneration','feedback'):
        branch=[r for r in generated if r['arm']==arm];branch_usage=usage(branch)
        full={k:shared_usage[k]+branch_usage[k] if shared_usage[k] is not None and branch_usage[k] is not None else None for k in keys}
        split={k:shared_usage[k]/2+branch_usage[k] if shared_usage[k] is not None and branch_usage[k] is not None else None for k in keys}
        passes=sum(r['status']=='PASS' for r in rows if r['arm']==arm)
        arms[arm]=dict(planned_branch_slots=8,branch_generated=len(branch),branch_statuses=dict(Counter(r['status'] for r in rows if r['arm']==arm)),
                       strategy_call_opportunities=16,shared_first_plus_branch_usage=full,half_shared_allocated_usage=split,branch_usage=branch_usage,
                       shared_plus_branch_elapsed_seconds=sum(r['generation']['elapsed_seconds'] for r in shared+branch),
                       pass_per_1000_allocated_output_tokens=passes*1000/split['output_tokens'] if split['output_tokens'] else None)
    batch.atomic(run/'summary.json',dict(planned_unique_calls=24,started=len(list((run/'jobs').glob('*/started.json'))),generated=len(generated),statuses=dict(Counter(r['status'] for r in rows)),
        first_candidate_statuses=dict(Counter(r['status'] for r in rows if r['role']=='first')),effects=dict(Counter(c['effect'] for c in comparisons)),comparisons=comparisons,
        families={t:[c for c in comparisons if c['task']==t] for t in tasks.TASKS},actual_unique_usage=usage(generated),shared_first_usage=shared_usage,arms=arms,cost='UNKNOWN',yosys='NOT_RUN',
        limitations='8 pairs in 4 development families; no token-length filtering, no strict compute matching; per-strategy shared cost cannot be summed as actual calls'))

def seal(run):
    # Exclude the mutable OS lock; safe even while caller holds it on Windows.
    assert not (run/'evidence-lock.json').exists()
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')})

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','verify','run']);p.add_argument('--execute-approved-plan-sha');args=p.parse_args()
    if args.command=='prepare':prepare();print('PREPARED 24 slots; 0 model calls');return
    plan=verify()
    if args.command=='verify':print('LOCKS_PASS; 0 model calls');return
    assert args.execute_approved_plan_sha==batch.read(RUN/'plan-lock.json')['sha256'],'Explicit controller release of this exact plan required'
    assert not (RUN/'evidence-lock.json').exists(),'Sealed campaign cannot restart'
    with batch.lock(RUN):
        dispatch=campaign(RUN,plan);batch.atomic(RUN/'dispatch.json',dispatch)
        if plan['source_hashes']==hashes():score(RUN,plan)
        else:batch.atomic(RUN/'scoring-blocked.json',dict(status='SOURCE_CHANGED',reason='No scoring with changed source/assets'))
        seal(RUN)
if __name__=='__main__':main()
