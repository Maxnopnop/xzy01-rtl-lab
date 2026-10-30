"""Public-evasive bounded FSM fixture; never a model-generated result."""
import sys,copy,random,time
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import batch,rtl_lab as lab,mutation_study as ms,paired_bank as bank,fsm_ir

def clone(ref,word):
    obj=copy.deepcopy(ref['data']);state=ref['reset']['state'];states=[state]
    for b in word:state=ref['edges'][state,int(b)];states.append(state)
    obj['reset']['state']='P0'
    for i,s in enumerate(states):
        obj['states'].append(dict(name='P'+str(i),output=ref['outputs'][s]^(i==len(word))))
        for b in (0,1):
            dest='P'+str(i+1) if i<len(word) and b==int(word[i]) else ref['edges'][s,b]
            obj['transitions'].append({'from':'P'+str(i),'input':b,'to':dest})
    return obj

def main():
    run=HERE/'runs/delayed-v1'
    if run.exists():raise ValueError('Immutable run exists')
    run.mkdir(parents=True);start=time.monotonic();rng=random.Random(20261011)
    specs=ms.development_specs();profiles=batch.read(ROOT/'evidence/mutation-v1/contracts-v2.json');cases=[]
    for spec in specs:
        task=spec['id'];ref=bank.graph(task)
        for _ in range(100):
            word=''.join(str(rng.randrange(2)) for _ in range(12))
            if not any(e['bits'].startswith(word) for e in profiles[task]['contract']['examples']):break
        else:raise RuntimeError('Cannot choose prefix')
        obj=clone(ref,word);ir=fsm_ir.parse(ms.raw(obj));diag=fsm_ir.product_check(ir,ref)
        assert diag['shortest_counterexample']['bits']==word
        assert diag['shortest_counterexample']['expected']==bank.oracle(task,[(0,0)]+[(1,int(b)) for b in word])[-1][3]
        cases.append(dict(task=task,word=word,ir=obj,diagnosis=diag))
    batch.atomic(run/'cases.json',cases)
    paths=[Path(__file__),HERE/'DELAYED_PROTOCOL.md',ROOT/'fsm_ir.py',ROOT/'fsm_checks.py',ROOT/'mutation_study.py',ROOT/'paired_bank.py',ROOT/'rtl_lab.py',ROOT/'backends.py',ROOT/'evidence/mutation-v1/contracts-v2.json',bank.ROOT/'bank-lock.json']
    batch.atomic(run/'plan.json',dict(kind='OFFLINE_PUBLIC_EVASIVE_PREFIX_FAULT',seed=20261011,new_model_calls=0,case_sha256=lab.digest((run/'cases.json').read_bytes()),source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths},planned=5,private_score_used_for_selection=False))
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10)
    tools=lab.inspect_tools(args,run);batch.atomic(run/'environment.json',tools);rows=[]
    for spec,case in zip(specs,cases):
        if time.monotonic()-start>120:raise RuntimeError('Wall cap')
        task=spec['id'];ir=fsm_ir.parse(ms.raw(case['ir']));ref=bank.graph(task);rtl=bank.fixture_rtl(ir,spec['ports'],spec['module']);folder=run/task
        public=bank.feedback(ms.raw(case['ir']),profiles[task]['contract'])
        assert public['status']=='PUBLIC_CHECK_PASS'
        fixed=ms.fixed_sim(folder/'fixed',spec,rtl,tools,args)
        agree=ms.agreement_sim(folder/'agreement',spec,ir,rtl,batch.read(bank.ROOT/task/'inputs.json'),tools,args)
        witness=ms.agreement_sim(folder/'witness',spec,ref,rtl,[(0,0)]+[(1,int(b)) for b in case['word']],tools,args)
        assert fixed['status'] in ('PASS','FUNCTION_FAIL');assert agree['status']=='PASS';assert witness['status']=='FUNCTION_FAIL'
        row=dict(task=task,word=case['word'],states=len(ir['outputs']),diagnosis=case['diagnosis'],public=public,fixed=fixed,agreement=agree,witness=witness,localization=fsm_ir.localize(case['diagnosis']['status'],fixed['status'],agree['status']))
        rows.append(row);print(task,public['status'],fixed['status'],row['localization'],flush=True)
    batch.atomic(run/'summary.json',dict(kind='OFFLINE_PUBLIC_EVASIVE_PREFIX_FAULT',planned=5,public_misses=sum(r['public']['status']=='PUBLIC_CHECK_PASS' for r in rows),fixed_misses=sum(r['fixed']['status']=='PASS' for r in rows),witness_detections=5,elapsed_seconds=time.monotonic()-start,model_calls=0,rows=rows,limits='Deliberately public-evasive artificial fixtures; no natural occurrence rate, no LLM efficacy estimate. Original frozen private scores unchanged.'))
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
if __name__=='__main__':main()
