"""Frozen 20-slot feedback study. prepare is offline; run requires plan hash."""
import sys,json,time,copy,argparse
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import batch,rtl_lab as lab,paired_bank as bank,paired_study as ps,mutation_study as ms,codex_network_adapter as adapter
TASKS=['rt_sequence','sticky_alarm','event_parity','request_delay','debounce3']
RUN=HERE/'runs/r2-prepared-v1'

def sources():
    paths=[Path(__file__),HERE/'R2_PROTOCOL.md',ROOT/'codex_network_adapter.py',ROOT/'codex_adapter.py',ROOT/'batch.py',ROOT/'rtl_lab.py',ROOT/'backends.py',ROOT/'paired_study.py',ROOT/'paired_bank.py',ROOT/'fsm_ir.py',ROOT/'fsm_checks.py',ROOT/'fsm_study.py',ROOT/'mutation_study.py',ROOT/'evidence/mutation-v1/contracts-v2.json']
    paths+=sorted(p for p in bank.ROOT.rglob('*') if p.is_file())
    return {str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths}

def prepare(run=RUN):
    assert not run.exists(),'Choose a new empty run'
    data=bank.load();profiles=batch.read(ROOT/'evidence/mutation-v1/contracts-v2.json');jobs=[]
    run.mkdir(parents=True)
    for repeat in (1,2):
        for i,task in enumerate(TASKS):
            case=next(c for c in data['cases'] if c['id']==('real_overlap' if task=='rt_sequence' else task+'_transition'))
            spec=copy.deepcopy(next(s for s in data['tasks'] if s['id']==task));spec['public_contract']=profiles[task]['contract']
            raw=(bank.ROOT/case['ir_file']).read_text(encoding='utf-8');common=ps.prompt(spec,raw,'control');feedback=ps.prompt(spec,raw,'feedback')
            assert common.endswith('\n'+__import__('fsm_study').NO_TOOLS)
            for arm in (('regeneration','feedback') if (repeat+i)%2 else ('feedback','regeneration')):
                jid=f'{task}__r{repeat}__{arm}';folder=run/'prompts'/jid;folder.mkdir(parents=True)
                text=common if arm=='regeneration' else feedback
                for name,value in [('prompt.txt',text),('common.txt',common),('candidate.txt',raw)]: (folder/name).write_bytes(value.encode('utf-8'))
                jobs.append(dict(id=jid,pair=task+'__r'+str(repeat),task=task,repeat=repeat,arm=arm,case=case,spec=spec,ir=raw,prompt=text,
                                 prompt_sha256=lab.digest(text.encode()),common_sha256=lab.digest(common.encode()),candidate_sha256=lab.digest(raw.encode())))
    plan=dict(kind='R2_PUBLIC_FEEDBACK_VS_REGENERATION',created_utc=lab.utc(),max_calls=20,retries=0,workers=1,
              model='gpt-5.6-sol',reasoning='low',api_timeout=180,jobs=jobs,source_hashes=sources())
    batch.atomic(run/'plan.json',plan);batch.atomic(run/'plan-lock.json',dict(sha256=lab.digest((run/'plan.json').read_bytes())))
    batch.atomic(run/'preparation-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
    return plan

def verify(run):
    assert lab.digest((run/'plan.json').read_bytes())==batch.read(run/'plan-lock.json')['sha256']
    plan=batch.read(run/'plan.json');assert plan['source_hashes']==sources(),'Source/asset change: do not execute'
    for rel,h in batch.read(run/'preparation-lock.json').items():assert lab.digest((run/rel).read_bytes())==h,rel
    assert len(plan['jobs'])==plan['max_calls']==20
    return plan

def generate(run,job,plan,call=None):
    folder=run/'jobs'/job['id'];folder.mkdir(parents=True,exist_ok=True)
    if (folder/'generation.json').exists():return batch.read(folder/'generation.json')
    if (folder/'started.json').exists():
        row=dict(status='UNKNOWN_INTERRUPTED',usage=None)
    else:
        spent=sum(batch.read(p)['reserved_calls'] for p in (run/'jobs').glob('*/started.json'))
        assert spent<plan['max_calls'];batch.atomic(folder/'started.json',dict(reserved_calls=1,utc=lab.utc()))
        c=folder/'call';c.mkdir();(c/'exact-prompt.txt').write_bytes(job['prompt'].encode());start=time.monotonic()
        args=SimpleNamespace(codex_executable=None,model=plan['model'],codex_reasoning=plan['reasoning'],api_timeout=plan['api_timeout'])
        try:
            output,meta=(call or adapter.generate_text)(args,c,job['prompt'])
            assert meta.get('tools_used') is False
            (folder/'response.txt').write_bytes(output.encode());row=dict(status='GENERATED',response_sha256=lab.digest(output.encode()),**meta)
        except lab.LabError as exc:row=dict(status=exc.status,stage=exc.stage,message=exc.message,usage=None)
        except Exception as exc:row=dict(status='ENV_ERROR',message=str(exc),usage=None)
        row['elapsed_seconds']=time.monotonic()-start
    batch.atomic(folder/'generation.json',row);return row

def campaign(run,plan,call=None):
    # Any unresolved or failed reservation blocks further dispatch on resume.
    for p in (run/'jobs').glob('*/started.json'):
        g=p.parent/'generation.json'
        if not g.exists():batch.atomic(g,dict(status='UNKNOWN_INTERRUPTED',usage=None))
        if batch.read(g)['status']!='GENERATED':return dict(status='STOPPED_INFRASTRUCTURE',gate=False)
    gate=False
    for index,job in enumerate(plan['jobs']):
        r=generate(run,job,plan,call)
        if r['status']!='GENERATED':return dict(status='STOPPED_INFRASTRUCTURE',gate=gate)
        if index==3:gate=True;batch.atomic(run/'gate.json',dict(passed=True,criterion='4 successful generations; no scoring used'))
    return dict(status='GENERATION_COMPLETE',gate=gate)

def score(run,plan):
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10);tools=lab.inspect_tools(args,run);rows=[]
    for j in plan['jobs']:
        folder=run/'jobs'/j['id'];g=folder/'generation.json';row={k:j[k] for k in ('id','pair','task','repeat','arm')};row['case_kind']=j['case']['kind']
        if not g.exists():row.update(status='PENDING',usage=None)
        else:
            gen=batch.read(g);row['generation']=gen;row['usage']=gen.get('usage')
            if gen['status']=='GENERATED':
                assert lab.digest((folder/'response.txt').read_bytes())==gen['response_sha256']
                result=folder/'judge.json'
                if not result.exists():batch.atomic(result,ps.judge(folder,j['spec'],(folder/'response.txt').read_text(encoding='utf-8'),j['ir'],tools,args))
                row.update(batch.read(result))
            else:row['status']=gen['status']
        row['yosys']='NOT_RUN';rows.append(row)
    comparisons=[];valid={'PASS','FUNCTION_FAIL','COMPILE_FAIL'}
    for pair in dict.fromkeys(j['pair'] for j in plan['jobs']):
        a=next(r for r in rows if r['pair']==pair and r['arm']=='regeneration');b=next(r for r in rows if r['pair']==pair and r['arm']=='feedback')
        effect='inconclusive' if a['status'] not in valid or b['status'] not in valid else ('help' if a['status']!='PASS' and b['status']=='PASS' else 'harm' if a['status']=='PASS' and b['status']!='PASS' else 'no_change')
        tokens=[(r.get('usage') or {}).get('output_tokens') for r in (a,b)]
        matched=all(isinstance(t,(int,float)) and t>0 for t in tokens) and max(tokens)/min(tokens)<=2
        comparisons.append(dict(pair=pair,task=a['task'],kind=a['case_kind'],effect=effect,output_token_ratio_le2=matched))
    summary=dict(planned=20,started=len(list((run/'jobs').glob('*/started.json'))),statuses=dict(Counter(r['status'] for r in rows)),rows=rows,comparisons=comparisons,
                 task_clusters={t:[c for c in comparisons if c['task']==t] for t in TASKS},cost='UNKNOWN',limitations='Conditional fixed-IR experiment; equal call opportunities, no hard token cap; small development-family sample')
    batch.atomic(run/'summary.json',summary)
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','verify','run']);p.add_argument('--execute-approved-plan-sha');a=p.parse_args()
    if a.command=='prepare':prepare();print('PREPARED: 20 slots; 0 model calls');return
    plan=verify(RUN)
    if a.command=='verify':print('LOCKS_PASS; 0 model calls');return
    assert a.execute_approved_plan_sha==batch.read(RUN/'plan-lock.json')['sha256'],'Explicit controller release and exact plan SHA required'
    with batch.lock(RUN):
        batch.atomic(RUN/'dispatch.json',campaign(RUN,plan));score(RUN,plan)
if __name__=='__main__':main()
