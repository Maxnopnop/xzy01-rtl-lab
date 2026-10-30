"""Versioned development-only compound-fault and metamorphic exploration."""
import copy, itertools, json, sys, time
from pathlib import Path
from collections import Counter
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
import batch, rtl_lab as lab, mutation_study as ms, paired_bank as bank, fsm_ir

def dump(p,x): batch.atomic(p,x)
def locus(a,b):
    edits=[]
    for group in ('states','transitions'):
        for i,(x,y) in enumerate(zip(a[group],b[group])):
            for k in x:
                if x[k]!=y[k]: edits.append((group,i,k,y[k]))
    for k in a['reset']:
        if a['reset'][k]!=b['reset'][k]: edits.append(('reset',k,b['reset'][k]))
    assert len(edits)==1
    return edits[0]

def combine(obj,a,b):
    x=copy.deepcopy(obj)
    for e in (a,b):
        if e[0]=='reset': x['reset'][e[1]]=e[2]
        else: x[e[0]][e[1]][e[2]]=e[3]
    return x

def transformations(obj):
    x=copy.deepcopy(obj); names={s['name']:'R'+str(i) for i,s in enumerate(reversed(x['states']))}
    for s in x['states']: s['name']=names[s['name']]
    for e in x['transitions']:
        e['from']=names[e['from']];e['to']=names[e['to']]
    x['reset']['state']=names[x['reset']['state']]
    yield 'rename',x
    x=copy.deepcopy(obj);x['states'].reverse();x['transitions'].reverse()
    yield 'reorder',x
    x=copy.deepcopy(obj);x['states'].append(dict(name='UNREACHABLE',output=1))
    x['transitions'] += [dict(**{'from':'UNREACHABLE','input':b,'to':'UNREACHABLE'}) for b in (0,1)]
    yield 'unreachable',x

def main():
    run=HERE/'runs'/'compound-v1'
    if run.exists(): raise ValueError('Immutable run exists')
    run.mkdir(parents=True)
    start=time.monotonic(); args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10)
    tools=lab.inspect_tools(args,run);dump(run/'environment.json',tools)
    specs=ms.development_specs();profiles=batch.read(ROOT/'evidence/mutation-v1/contracts-v2.json')
    paths=[Path(__file__),HERE/'PROTOCOL.md',ROOT/'fsm_ir.py',ROOT/'paired_bank.py',ROOT/'mutation_study.py',ROOT/'rtl_lab.py',ROOT/'backends.py',ROOT/'fsm_checks.py',ROOT/'batch.py',ROOT/'evidence/mutation-v1/contracts-v2.json',bank.ROOT/'bank-lock.json']
    plan=dict(version=1,created_utc=lab.utc(),kind='OFFLINE_COMPOUND_FIXTURES',new_model_calls=0,seed=None,selection='All distinct-locus pairs, JSON dedup; simulation first10 faults/family plus v2 misses capped100',tasks=[s['id'] for s in specs],source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths},max_variants=10000,wall_seconds=1200,disk_bytes=500*1024**2)
    dump(run/'plan.json',plan)
    calibrations=[]
    for spec in specs:
        ref=bank.graph(spec['id']);rtl=bank.fixture_rtl(ref,spec['ports'],spec['module'])
        row=ms.fixed_sim(run/'calibration'/spec['id'],spec,rtl,tools,args)
        assert row['status']=='PASS',row
        calibrations.append(dict(task=spec['id'],**row))
    dump(run/'calibration.json',dict(seconds=time.monotonic()-start,rows=calibrations))
    print('CALIBRATION',round(time.monotonic()-start,2),flush=True)
    allrows=[];summary=[];simulations=[];metas=[]
    for spec in specs:
        task=spec['id'];ref=bank.graph(task);original=ref['data']
        singles=[(ident,kind,locus(original,obj)) for ident,kind,obj in ms.mutations(ref)]
        rows=[];seen=set()
        for (ai,ak,a),(bi,bk,b) in itertools.combinations(singles,2):
            if a[:-1]==b[:-1]:continue
            obj=combine(original,a,b);raw=ms.raw(obj)
            if raw in seen:continue
            seen.add(raw);ir=fsm_ir.parse(raw);diag=fsm_ir.product_check(ir,ref)
            ce=diag['shortest_counterexample']
            if ce:
                bits=ce['bits'];inp=[(0,0)]+[(1,int(c)) for c in bits]
                expected=bank.oracle(task,inp)[-1][3]
                assert expected==ce['expected']
                assert fsm_ir.trace(ir,bits)[-1] != expected if bits else ir['outputs'][ir['reset']['state']]!=expected
            p1=bank.feedback(raw,spec['public_contract'])['status'];p2=bank.feedback(raw,profiles[task]['contract'])['status']
            rows.append(dict(id=task+'__'+ai+'__'+bi,task=task,operators=[ak,bk],ir=obj,diagnosis=diag,is_fault=diag['status']=='IR_SPEC_MISMATCH',public_v1=p1,public_v2=p2))
        assert len(allrows)+len(rows)<=10000
        faults=[r for r in rows if r['is_fault']];miss=[r for r in faults if r['public_v2']=='PUBLIC_CHECK_PASS']
        selected={r['id']:r for r in faults[:10]+miss[:100]}
        for r in selected.values():
            if time.monotonic()-start>1200:raise RuntimeError('Wall cap')
            ir=fsm_ir.parse(ms.raw(r['ir']));rtl=bank.fixture_rtl(ir,spec['ports'],spec['module']);folder=run/'simulations'/r['id']
            fixed=ms.fixed_sim(folder/'spec',spec,rtl,tools,args)
            agree=ms.agreement_sim(folder/'agreement',spec,ir,rtl,batch.read(bank.ROOT/task/'inputs.json'),tools,args)
            assert agree['status']=='PASS';assert fixed['status'] in ('PASS','FUNCTION_FAIL')
            simulations.append(dict(id=r['id'],task=task,fixed=fixed,agreement=agree))
        for ident,obj in transformations(original):
            ir=fsm_ir.parse(ms.raw(obj));diag=fsm_ir.product_check(ir,ref)
            assert diag['status']=='IR_EQUIVALENT'
            p=bank.feedback(ms.raw(obj),profiles[task]['contract'])
            assert p['status']=='PUBLIC_CHECK_PASS'
            fixed=ms.fixed_sim(run/'metamorphic'/(task+'__'+ident),spec,bank.fixture_rtl(ir,spec['ports'],spec['module']),tools,args)
            assert fixed['status']=='PASS'
            metas.append(dict(task=task,transform=ident,ir=obj,public=p,diagnosis=diag,fixed=fixed))
        summary.append(dict(task=task,variants=len(rows),faults=len(faults),equivalent=len(rows)-len(faults),v1_misses=sum(r['public_v1']=='PUBLIC_CHECK_PASS' for r in faults),v2_misses=len(miss),help=sum(r['public_v1']=='PUBLIC_CHECK_PASS' and r['public_v2']=='PUBLIC_CHECK_FAIL' for r in faults),harm=sum(r['public_v1']=='PUBLIC_CHECK_FAIL' and r['public_v2']=='PUBLIC_CHECK_PASS' for r in faults),simulated=len(selected),miss_sim_truncated=max(0,len(miss)-100)))
        allrows+=rows;dump(run/'cases.json',allrows);dump(run/'simulation-results.json',simulations);dump(run/'metamorphic-results.json',metas)
        print(json.dumps(summary[-1]),flush=True)
    dump(run/'summary.json',dict(kind=plan['kind'],coverage=summary,variants=len(allrows),simulation_statuses=dict(Counter(r['fixed']['status'] for r in simulations)),agreement_statuses=dict(Counter(r['agreement']['status'] for r in simulations)),metamorphic_passes=len(metas),elapsed_seconds=time.monotonic()-start,model_calls=0,token_usage=None,cost=0,limits='Five development families; fixtures, not LLM gains. No final-set claim. Simulation is selected, graph enumeration is complete.'))
    dump(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
if __name__=='__main__':main()
