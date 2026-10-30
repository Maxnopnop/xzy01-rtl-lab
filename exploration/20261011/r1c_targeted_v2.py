"""Supplemental calibration isolates mid-run reset and non-reset hold failures."""
import sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import timed_reset as tr,r1b_v2,mutation_study as ms,batch,rtl_lab as lab
def main():
    run=HERE/'runs/timed-calibration-v2';assert not run.exists();run.mkdir()
    spec=next(s for s in ms.development_specs() if s['id']=='event_parity')
    base=r1b_v2.reference('event_parity',spec['module'],spec['ports'])
    # Initialize synchronous mutant with a real edge under reset, then parity=1.
    values=[(1,0,0,0),(1,0,0,0),(0,1,0,0),(1,1,1,1),(0,1,1,1),(0,0,1,0),(0,1,1,0)]
    mid=[dict(clk=c,reset=r,bit=b,expected=q,category='targeted_mid_reset' if i==5 else 'setup') for i,(c,r,b,q) in enumerate(values)]
    hold=[dict(clk=c,reset=r,bit=b,expected=q,category='targeted_hold' if i==3 else 'setup') for i,(c,r,b,q) in enumerate([(0,0,0,0),(1,0,0,0),(0,1,0,0),(0,1,1,0)])]
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10);tools=lab.inspect_tools(args,run)
    results=[]
    for name,text,events,expected in [('correct_mid',base,mid,'PASS'),('sync_mid',base.replace(' or negedge rst_n',''),mid,'FUNCTION_FAIL'),('correct_hold',base,hold,'PASS'),('leak_hold',base.replace('q=parity','q=parity^din'),hold,'FUNCTION_FAIL')]:
        r=tr.simulate(run/name,spec,text.encode(),events,tools,args);assert r['status']==expected
        if r['mismatches']:assert r['mismatches'][0]['category']==('targeted_mid_reset' if name=='sync_mid' else 'targeted_hold') and r['mismatches'][0]['observed'] in ('0','1')
        results.append(dict(label=name,**r))
    batch.atomic(run/'summary.json',dict(icarus_evaluations=4,model_calls=0,results=results))
    batch.atomic(run/'plan.json',dict(source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in [Path(__file__),HERE/'timed_reset.py',HERE/'r1b_v2.py']},events=dict(mid=mid,hold=hold),reason='Supplemental isolated calibration; frozen broad calibration and historical run unchanged'))
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
    print([(r['label'],r['status'],r['mismatches'][:1]) for r in results])
if __name__=='__main__':main()
