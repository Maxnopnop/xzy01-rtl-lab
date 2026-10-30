"""R4 prepare-gated 48 unique calls; model-produced intents only in real campaign."""
import sys,json,time,argparse
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];V3=BASE.parent/'r3-runner-v3'
sys.path[:0]=[str(BASE),str(ROOT),str(V3)]
import tasks,intent,prompts,judge,batch,rtl_lab as lab,cli_adapter as adapter
RUN=BASE/'runs/prepared-v1';ASSETS=BASE/'assets-v1'
FUNCTIONAL={'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED','EXTRACTION_ERROR','IR_INVALID','UNSUPPORTED','INPUT_LIMIT'}
MAX_INPUT=256*1024
def hashes():
    paths=sorted(BASE.glob('*.py'))+[BASE/'PROTOCOL.md']+sorted((BASE/'references').glob('*.sv'))+sorted(ASSETS.glob('*.json'))
    paths+=[V3/'cli_adapter.py',V3/'stdin_process.py']+[ROOT/n for n in ('rtl_lab.py','backends.py','batch.py','fsm_study.py')]
    return {str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths}
def plan():
    cases=[];jobs=[]
    for repeat in (1,2):
        for i,task in enumerate(tasks.TASKS):
            case=f'{task}__r{repeat}';cases.append(dict(id=case,task=task,repeat=repeat))
            representations=['structured','linear'] if (i+repeat)%2 else ['linear','structured']
            for representation in representations:
                jid=case+'__'+representation+'__intent';jobs.append(dict(id=jid,case=case,task=task,representation=representation,role='intent',arm='shared',prompt=prompts.intention(task,representation)))
            for representation in representations:
                prefix=case+'__'+representation
                jobs.append(dict(id=prefix+'__first',case=case,task=task,representation=representation,role='first_rtl',arm='shared',intent_id=prefix+'__intent'))
            for representation in reversed(representations):
                arms=['feedback','regeneration'] if (i+repeat)%2 else ['regeneration','feedback']
                for arm in arms:
                    prefix=case+'__'+representation
                    jobs.append(dict(id=prefix+'__'+arm,case=case,task=task,representation=representation,role='branch',arm=arm,intent_id=prefix+'__intent',first_id=prefix+'__first'))
    return dict(kind='R4_PREPARATION_NOT_RELEASE',created_utc=lab.utc(),model='gpt-5.6-sol',reasoning='low',api_timeout=180,max_calls=48,workers=1,retries=0,wall_budget_seconds=10800,disk_budget_bytes=750*1024*1024,input_byte_limit=MAX_INPUT,cases=cases,jobs=jobs,source_hashes=hashes())
def prepare():
    assert batch.read(BASE/'runs/calibration-v3/summary.json')['status']=='PASS'
    assert batch.read(BASE/'runs/control-v1/summary.json')['status']=='PASS'
    assert not RUN.exists();RUN.mkdir(parents=True);p=plan()
    for j in p['jobs']:
        if 'prompt' in j:
            folder=RUN/'prompts'/j['id'];folder.mkdir(parents=True);(folder/'prompt.txt').write_bytes(j['prompt'].encode())
            j['prompt_sha256']=lab.digest(j['prompt'].encode())
    batch.atomic(RUN/'plan.json',p);batch.atomic(RUN/'plan-lock.json',dict(sha256=lab.digest((RUN/'plan.json').read_bytes())))
    batch.atomic(RUN/'preparation-lock.json',{str(x.relative_to(RUN)):lab.digest(x.read_bytes()) for x in RUN.rglob('*') if x.is_file()})
def verify():
    p=batch.read(RUN/'plan.json');assert lab.digest((RUN/'plan.json').read_bytes())==batch.read(RUN/'plan-lock.json')['sha256']
    assert p['source_hashes']==hashes()
    for rel,h in batch.read(RUN/'preparation-lock.json').items():assert lab.digest((RUN/rel).read_bytes())==h
    assert len(p['jobs'])==48 and len(p['cases'])==6
    return p
def raw(run,jid):
    folder=run/'jobs'/jid;data=(folder/'response.txt').read_bytes();g=batch.read(folder/'generation.json')
    assert lab.digest(data)==g['response_sha256'];return data.decode('utf-8')
def generate(run,job,p,prompt,call=None):
    folder=run/'jobs'/job['id'];folder.mkdir(parents=True,exist_ok=True);g=folder/'generation.json'
    if g.exists():return batch.read(g)
    if (folder/'started.json').exists():result=dict(status='UNKNOWN_INTERRUPTED',usage=None)
    elif len(prompt.encode())>p['input_byte_limit']:
        (folder/'response.txt').write_bytes(b'');(folder/'exact-prompt.txt').write_bytes(prompt.encode())
        result=dict(status='INPUT_LIMIT',usage=None,response_sha256=lab.digest(b''),prompt_sha256=lab.digest(prompt.encode()),prompt_bytes=len(prompt.encode()),model_called=False)
    else:
        if len(list((run/'jobs').glob('*/started.json')))>=p['max_calls']:return dict(status='BUDGET_STOP',usage=None)
        batch.atomic(folder/'started.json',dict(utc=lab.utc(),reserved_calls=1));c=folder/'call';c.mkdir();(c/'exact-prompt.txt').write_bytes(prompt.encode());start=time.monotonic()
        args=SimpleNamespace(codex_executable=None,model=p['model'],codex_reasoning=p['reasoning'],api_timeout=p['api_timeout'])
        try:
            response,meta=(call or adapter.generate_text)(args,c,prompt);(folder/'response.txt').write_bytes(response.encode())
            result=dict(status='GENERATED' if meta.get('tools_used') is False else 'RTL_REJECTED',**meta)
        except lab.LabError as e:
            result=dict(status=e.status,stage=e.stage,message=e.message,usage=None)
            if e.status in FUNCTIONAL:
                output=c/'model_output.raw.txt';(folder/'response.txt').write_bytes(output.read_bytes() if output.exists() else b'')
        except Exception as e:result=dict(status='ENV_ERROR',message=str(e),usage=None)
        result.update(elapsed_seconds=time.monotonic()-start,prompt_bytes=len(prompt.encode()),prompt_sha256=lab.digest(prompt.encode()),model_called=True)
        if (folder/'response.txt').exists():result['response_sha256']=lab.digest((folder/'response.txt').read_bytes());result['response_bytes']=(folder/'response.txt').stat().st_size
    batch.atomic(g,result);return result
def public_feedback(task,representation,ri,rtl,rows,folder):
    folder.mkdir(parents=True,exist_ok=True);ir,values=intent.check(ri,representation,task,rows)
    spec=judge.public_feedback(task,rtl,rows,folder/'rtl-spec')
    alignment=judge.public_feedback(task,rtl,[dict(r,expected=v) for r,v in zip(rows,values)],folder/'rtl-intent') if values is not None else dict(status='NOT_ASSESSABLE',mismatches=[])
    return dict(intent_spec=ir,rtl_spec=spec,rtl_intent=alignment,scope='Public events only; no private reference or hidden tests')
def campaign(run,p,call=None,feedback=None,check_sources=True):
    for reservation in (run/'jobs').glob('*/started.json'):
        g=reservation.parent/'generation.json'
        if not g.exists():batch.atomic(g,dict(status='UNKNOWN_INTERRUPTED',usage=None))
        if batch.read(g)['status'] not in FUNCTIONAL|{'GENERATED'}:return dict(status='STOPPED_INFRASTRUCTURE',reason='Prior unknown/failed reservation')
    start=run/'dispatch-start.json'
    if not start.exists():batch.atomic(start,dict(epoch=time.time()))
    for index,j in enumerate(p['jobs']):
        if check_sources and p['source_hashes']!=hashes():return dict(status='SOURCE_CHANGED')
        if time.time()-batch.read(start)['epoch']>p['wall_budget_seconds'] or sum(x.stat().st_size for x in run.rglob('*') if x.is_file())>p['disk_budget_bytes']:return dict(status='BUDGET_STOP')
        if j['role']=='intent':prompt=j['prompt']
        else:
            ri=raw(run,j['intent_id'])
            if j['role']=='first_rtl':prompt=prompts.first(j['task'],j['representation'],ri)
            else:
                candidate=raw(run,j['first_id']);parent=run/'jobs'/j['first_id'];ff=parent/'public-feedback.json'
                if not ff.exists():batch.atomic(ff,(feedback or public_feedback)(j['task'],j['representation'],ri,candidate,batch.read(ASSETS/(j['task']+'-public.json')),parent/'public'))
                fb=batch.read(ff)
                if any(fb[k]['status'] not in FUNCTIONAL|{'NOT_ASSESSABLE'} for k in ('intent_spec','rtl_spec','rtl_intent')):return dict(status='STOPPED_INFRASTRUCTURE',reason='Public checker infrastructure')
                prompt=prompts.branch(j['task'],j['representation'],ri,candidate,fb if j['arm']=='feedback' else None)
        gen=generate(run,j,p,prompt,call)
        if gen['status'] not in FUNCTIONAL|{'GENERATED'}:return dict(status='BUDGET_STOP' if gen['status']=='BUDGET_STOP' else 'STOPPED_INFRASTRUCTURE',reason=gen['status'])
        if len(list((run/'jobs').glob('*/started.json')))==4 and gen.get('model_called'):batch.atomic(run/'gate.json',dict(passed=True,criterion='First four actual model calls returned without infrastructure failure; no functional/format filtering'))
    return dict(status='GENERATION_COMPLETE')
def score(run,p):
    results=[]
    for j in p['jobs']:
        row={k:v for k,v in j.items() if k!='prompt'};folder=run/'jobs'/j['id'];gf=folder/'generation.json'
        if not gf.exists():row.update(status='PENDING',generation=None,judge=None)
        else:
            gen=batch.read(gf);row['generation']=gen
            if gen['status']!='GENERATED':row.update(status=gen['status'],judge=None)
            else:
                jf=folder/'hidden-judge.json'
                if not jf.exists():
                    rows=batch.read(ASSETS/(j['task']+'-private.json'))
                    if j['role']=='intent':checks=dict(intent_spec=intent.check(raw(run,j['id']),j['representation'],j['task'],rows)[0])
                    else:
                        ir,values=intent.check(raw(run,j['intent_id']),j['representation'],j['task'],rows)
                        checks=dict(intent_spec=ir,rtl_spec=judge.simulate(folder/'hidden-spec',j['task'],raw(run,j['id']),rows),rtl_intent=judge.simulate(folder/'hidden-intent',j['task'],raw(run,j['id']),[dict(r,expected=v) for r,v in zip(rows,values)]) if values is not None else dict(status='NOT_ASSESSABLE',stage='alignment'))
                    batch.atomic(jf,checks)
                row['judge']=batch.read(jf);row['status']=row['judge']['intent_spec' if j['role']=='intent' else 'rtl_spec']['status']
        results.append(row)
    summary=summarize(results,p);batch.atomic(run/'results.json',results);batch.atomic(run/'summary.json',summary);return summary
def summarize(results,p):
    strategies={};comparisons=[];usage_keys=('input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens')
    def usage(rows):return {k:sum((r['generation'].get('usage') or {})[k] for r in rows) if rows and all(isinstance(((r.get('generation') or {}).get('usage') or {}).get(k),(int,float)) for r in rows) else None for k in usage_keys}
    for rep in ('structured','linear'):
        shared=[r for r in results if r['representation']==rep and r['arm']=='shared'];su=usage(shared)
        for arm in ('regeneration','feedback'):
            branches=[r for r in results if r['representation']==rep and r['arm']==arm];bu=usage(branches)
            strategies[rep+'_'+arm]=dict(denominator=6,passes=sum(r['status']=='PASS' for r in branches),statuses=dict(Counter(r['status'] for r in branches)),opportunities=18,allocated_calls=12,shared_full_usage={k:su[k]+bu[k] if su[k] is not None and bu[k] is not None else None for k in usage_keys},shared_half_usage={k:su[k]/2+bu[k] if su[k] is not None and bu[k] is not None else None for k in usage_keys})
        for case in p['cases']:
            arms={r['arm']:r for r in results if r['case']==case['id'] and r['representation']==rep and r['role']=='branch'}
            a=arms['regeneration']['status'];b=arms['feedback']['status']
            effect='inconclusive' if a not in FUNCTIONAL or b not in FUNCTIONAL else 'help' if a!='PASS' and b=='PASS' else 'harm' if a=='PASS' and b!='PASS' else 'no_change'
            comparisons.append(dict(case=case['id'],representation=rep,regeneration=a,feedback=b,effect=effect))
    # Keep three raw statuses and descriptive alignment category, never unique internal attribution.
    for r in results:
        if r['role']=='intent' or not r.get('judge'):continue
        a=r['judge']['intent_spec']['status'];b=r['judge']['rtl_spec']['status'];c=r['judge']['rtl_intent']['status']
        r['observation']='NOT_ASSESSABLE' if c=='NOT_ASSESSABLE' else 'ALL_MATCH' if a==b==c=='PASS' else 'BOTH_DIVERGE' if a!='PASS' and b!='PASS' and c!='PASS' else 'INTENT_DIVERGES_RTL_MATCHES_INTENT' if a!='PASS' and c=='PASS' else 'CORRECT_RTL_DIFFERENT_INTENT' if b=='PASS' and a!='PASS' else 'RTL_DIFFERENT_INTENT'
    return dict(planned_unique_calls=48,started=sum(bool((r.get('generation') or {}).get('model_called')) for r in results),statuses=dict(Counter(r['status'] for r in results)),intent_statuses=dict(Counter(r['status'] for r in results if r['role']=='intent')),first_rtl_statuses=dict(Counter(r['status'] for r in results if r['role']=='first_rtl')),strategies=strategies,comparisons=comparisons,effects=dict(Counter(c['effect'] for c in comparisons)),actual_unique_usage=usage([r for r in results if (r.get('generation') or {}).get('model_called')]),cost='UNKNOWN',observations=[dict(id=r['id'],category=r['observation']) for r in results if 'observation' in r],label='Model evidence only if actual real campaign; offline fixtures separately labeled')
def seal(run):
    assert not (run/'evidence-lock.json').exists();batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')})
def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','run']);parser.add_argument('--execute-approved-plan-sha');args=parser.parse_args()
    if args.command=='prepare':prepare();print('PREPARED; 0 model calls');return
    p=verify()
    if args.command=='verify':print('LOCKS_PASS; 0 model calls');return
    assert args.execute_approved_plan_sha==batch.read(RUN/'plan-lock.json')['sha256'],'New exact plan release required'
    assert not (RUN/'evidence-lock.json').exists()
    with batch.lock(RUN):
        dispatch=campaign(RUN,p);batch.atomic(RUN/'dispatch.json',dispatch)
        if p['source_hashes']==hashes():score(RUN,p)
        else:batch.atomic(RUN/'scoring-blocked.json',dict(status='SOURCE_CHANGED'))
        seal(RUN)
if __name__=='__main__':main()
