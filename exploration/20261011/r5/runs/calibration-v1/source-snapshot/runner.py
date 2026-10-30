"""R5 prepare-gated 48 unique calls; model-produced intents only in real campaign."""
import sys,json,time,argparse
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];V3=BASE.parent/'r3-runner-v3'
sys.path[:0]=[str(BASE),str(ROOT),str(V3)]
import tasks,intent,prompts,judge,batch,rtl_lab as lab,cli_adapter as adapter
RUN=BASE/'runs/prepared-v1';ASSETS=BASE/'assets'
FUNCTIONAL={'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED','EXTRACTION_ERROR','IR_INVALID','UNSUPPORTED','INPUT_LIMIT'}
MAX_INPUT=256*1024
def hashes():
    paths=sorted(BASE.glob('*.py'))+[BASE/'PROTOCOL.md']+sorted((BASE/'references').glob('*.sv'))+sorted(ASSETS.glob('*.json'))
    paths+=[V3/'cli_adapter.py',V3/'stdin_process.py']+[ROOT/n for n in ('rtl_lab.py','backends.py','batch.py','fsm_study.py')]
    return {str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths}
def generate(run,job,p,prompt,call=None):
    folder=run/'jobs'/job['id'];folder.mkdir(parents=True,exist_ok=True);g=folder/'generation.json'
    if g.exists():return batch.read(g)
    if (folder/'started.json').exists():result=dict(status='UNKNOWN_INTERRUPTED',usage=None,model_called=True,reservation_unknown=True)
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
# Assembled after frozen v3 adapter bindings and reviewed R4 generate reservation logic.
def plan():
    jobs=[];cases=[]
    for i,task in enumerate(tasks.TASKS):
        for repeat in (1,2):
            case=f'{task}__r{repeat}';cases.append(dict(id=case,task=task,repeat=repeat))
            s=case+'__structured';d=case+'__direct'
            firsts=[dict(id=s+'__intent',role='intent',representation='structured',prompt=prompts.intention(task)),dict(id=d+'__first',role='direct_first',representation='direct',prompt=prompts.direct(task))]
            if (i+repeat)%2:firsts.reverse()
            stages=[dict(id=s+'__first',role='first_rtl',representation='structured',intent_id=s+'__intent'),dict(id=d+'__second',role='direct_second',representation='direct',first_id=d+'__first')]
            if (i+repeat)%2:stages.reverse()
            for j in firsts+stages:jobs.append(dict(case=case,task=task,arm='shared',**j))
            for rep,prefix,parent in [('structured',s,s+'__first'),('direct',d,d+'__second')]:
                for arm in (['feedback','regeneration'] if (i+repeat)%2 else ['regeneration','feedback']):jobs.append(dict(id=prefix+'__'+arm,case=case,task=task,arm=arm,representation=rep,role='branch',first_id=parent,**({'intent_id':s+'__intent'} if rep=='structured' else {})))
    return dict(kind='R5_PREPARATION_NOT_RELEASE',created_utc=lab.utc(),model='gpt-5.6-sol',reasoning='low',api_timeout=180,max_calls=48,workers=1,retries=0,wall_budget_seconds=10800,disk_budget_bytes=750*1024*1024,input_byte_limit=MAX_INPUT,cases=cases,jobs=jobs,source_hashes=hashes())
def prepare():
    for name in ('calibration-v1','control-v1'):assert batch.read(BASE/'runs'/name/'summary.json')['status']=='PASS'
    assert not RUN.exists();RUN.mkdir(parents=True);p=plan()
    for j in p['jobs']:
        if 'prompt' in j:
            folder=RUN/'prompts'/j['id'];folder.mkdir(parents=True);(folder/'prompt.txt').write_bytes(j['prompt'].encode());j['prompt_sha256']=lab.digest(j['prompt'].encode())
    batch.atomic(RUN/'plan.json',p);batch.atomic(RUN/'plan-lock.json',dict(sha256=lab.digest((RUN/'plan.json').read_bytes())))
    batch.atomic(RUN/'preparation-lock.json',{str(x.relative_to(RUN)):lab.digest(x.read_bytes()) for x in RUN.rglob('*') if x.is_file()})
def verify():
    p=batch.read(RUN/'plan.json');assert lab.digest((RUN/'plan.json').read_bytes())==batch.read(RUN/'plan-lock.json')['sha256'];assert p['source_hashes']==hashes()
    for rel,h in batch.read(RUN/'preparation-lock.json').items():assert lab.digest((RUN/rel).read_bytes())==h
    assert len(p['jobs'])==48 and len(p['cases'])==6;return p
def raw(run,jid):
    folder=run/'jobs'/jid;data=(folder/'response.txt').read_bytes();g=batch.read(folder/'generation.json');assert lab.digest(data)==g['response_sha256'];return data.decode()
def public_feedback(task,rtl,rows,folder):return judge.public_feedback(task,rtl,rows,folder)
def campaign(run,p,call=None,feedback=None,check_sources=True):
    for reservation in (run/'jobs').glob('*/started.json'):
        g=reservation.parent/'generation.json'
        if not g.exists():batch.atomic(g,dict(status='UNKNOWN_INTERRUPTED',usage=None,model_called=True,reservation_unknown=True))
        if batch.read(g)['status'] not in FUNCTIONAL|{'GENERATED'}:return dict(status='STOPPED_INFRASTRUCTURE',reason='Prior unknown/failed reservation')
    if not (run/'dispatch-start.json').exists():batch.atomic(run/'dispatch-start.json',dict(epoch=time.time()))
    for j in p['jobs']:
        if check_sources and p['source_hashes']!=hashes():return dict(status='SOURCE_CHANGED')
        if time.time()-batch.read(run/'dispatch-start.json')['epoch']>p['wall_budget_seconds'] or sum(x.stat().st_size for x in run.rglob('*') if x.is_file())>p['disk_budget_bytes']:return dict(status='BUDGET_STOP')
        if 'prompt' in j:prompt=j['prompt']
        elif j['role']=='first_rtl':prompt=prompts.first(j['task'],'structured',raw(run,j['intent_id']))
        elif j['role']=='direct_second':prompt=prompts.second(j['task'],raw(run,j['first_id']))
        else:
            candidate=raw(run,j['first_id']);parent=run/'jobs'/j['first_id'];ff=parent/'public-feedback.json'
            if not ff.exists():batch.atomic(ff,(feedback or public_feedback)(j['task'],candidate,batch.read(ASSETS/(j['task']+'-public.json')),parent/'public'))
            fb=batch.read(ff)
            if fb['status'] not in FUNCTIONAL:return dict(status='STOPPED_INFRASTRUCTURE',reason='Public checker infrastructure')
            prompt=prompts.branch(j['task'],j['representation'],None,candidate,fb if j['arm']=='feedback' else None)
        gen=generate(run,j,p,prompt,call)
        if gen['status'] not in FUNCTIONAL|{'GENERATED'}:return dict(status='BUDGET_STOP' if gen['status']=='BUDGET_STOP' else 'STOPPED_INFRASTRUCTURE',reason=gen['status'])
        if len(list((run/'jobs').glob('*/started.json')))==4 and gen.get('model_called'):batch.atomic(run/'gate.json',dict(passed=True,criterion='Four reserved real returns without infrastructure error; no format/functional filtering'))
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
                    if j['role']=='intent':checks=dict(intent_spec=intent.check(raw(run,j['id']),'structured',j['task'],rows)[0])
                    else:
                        checks=dict(rtl_spec=judge.simulate(folder/'hidden-spec',j['task'],raw(run,j['id']),rows))
                        if j['representation']=='structured':
                            ir,values=intent.check(raw(run,j['intent_id']),'structured',j['task'],rows);checks['intent_spec']=ir
                            checks['rtl_intent']=judge.simulate(folder/'hidden-intent',j['task'],raw(run,j['id']),[dict(r,expected=v) for r,v in zip(rows,values)]) if values is not None else dict(status='NOT_ASSESSABLE',stage='alignment')
                    batch.atomic(jf,checks)
                row['judge']=batch.read(jf);row['status']=row['judge']['intent_spec' if j['role']=='intent' else 'rtl_spec']['status']
        results.append(row)
    summary=summarize(results,p);batch.atomic(run/'results.json',results);batch.atomic(run/'summary.json',summary);return summary
def summarize(results,p):
    strategies={};comparisons=[];keys=('input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens')
    def usage(rows):return {k:sum((r['generation'].get('usage') or {})[k] for r in rows) if rows and all(isinstance(((r.get('generation') or {}).get('usage') or {}).get(k),(int,float)) for r in rows) else None for k in keys}
    for rep in ('structured','direct'):
        shared=[r for r in results if r['representation']==rep and r['arm']=='shared'];su=usage(shared)
        for arm in ('regeneration','feedback'):
            branches=[r for r in results if r['representation']==rep and r['arm']==arm];bu=usage(branches)
            strategies[rep+'_'+arm]=dict(denominator=6,passes=sum(r['status']=='PASS' for r in branches),statuses=dict(Counter(r['status'] for r in branches)),opportunities=18,allocated_calls=12,shared_full_usage={k:su[k]+bu[k] if su[k] is not None and bu[k] is not None else None for k in keys},shared_half_usage={k:su[k]/2+bu[k] if su[k] is not None and bu[k] is not None else None for k in keys})
        for case in p['cases']:
            arms={r['arm']:r for r in results if r['case']==case['id'] and r['representation']==rep and r['role']=='branch'};a=arms['regeneration']['status'];b=arms['feedback']['status']
            effect='inconclusive' if a not in FUNCTIONAL or b not in FUNCTIONAL else 'help' if a!='PASS' and b=='PASS' else 'harm' if a=='PASS' and b!='PASS' else 'no_change'
            comparisons.append(dict(case=case['id'],representation=rep,regeneration=a,feedback=b,effect=effect))
    pairs=[]
    for case in p['cases']:
        for arm in ('regeneration','feedback'):
            pair={r['representation']:r['status'] for r in results if r['case']==case['id'] and r['arm']==arm};pairs.append(dict(case=case['id'],arm=arm,**pair))
    observations=[]
    for r in results:
        c=r.get('judge') or {}
        if 'rtl_intent' in c:
            a,b,d=(c[k]['status'] for k in ('intent_spec','rtl_spec','rtl_intent'));observations.append(dict(id=r['id'],intent_spec=a,rtl_spec=b,rtl_intent=d,category='NOT_ASSESSABLE' if d=='NOT_ASSESSABLE' else 'ALL_MATCH' if a==b==d=='PASS' else 'OBSERVABLE_DIVERGENCE'))
    return dict(planned_unique_calls=48,started=sum(bool((r.get('generation') or {}).get('model_called')) for r in results),statuses=dict(Counter(r['status'] for r in results)),role_statuses={role:dict(Counter(r['status'] for r in results if r['role']==role)) for role in ('intent','first_rtl','direct_first','direct_second','branch')},strategies=strategies,comparisons=comparisons,representation_pairs=pairs,effects=dict(Counter(c['effect'] for c in comparisons)),actual_unique_usage=usage([r for r in results if (r.get('generation') or {}).get('model_called')]),cost='UNKNOWN',observations=observations,label='OFFLINE fixtures never model evidence; reservation not confirmed provider usage')
def seal(run):
    assert not (run/'evidence-lock.json').exists();batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')})
def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','run']);parser.add_argument('--execute-approved-plan-sha');args=parser.parse_args()
    if args.command=='prepare':prepare();print('PREPARED; 0 model calls');return
    p=verify()
    if args.command=='verify':print('LOCKS_PASS; 0 model calls');return
    assert args.execute_approved_plan_sha==batch.read(RUN/'plan-lock.json')['sha256'],'New exact R5 plan release required';assert not (RUN/'evidence-lock.json').exists()
    with batch.lock(RUN):
        batch.atomic(RUN/'dispatch.json',campaign(RUN,p))
        if p['source_hashes']==hashes():score(RUN,p)
        else:batch.atomic(RUN/'scoring-blocked.json',dict(status='SOURCE_CHANGED'))
    seal(RUN)
if __name__=='__main__':main()
