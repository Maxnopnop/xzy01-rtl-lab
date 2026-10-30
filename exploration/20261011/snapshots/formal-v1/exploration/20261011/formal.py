"""Existing Yosys internal bounded SAT, tick-level reset semantics only."""
import sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import batch,rtl_lab as lab,paired_bank as bank,mutation_study as ms,fsm_ir

def main():
    run=HERE/'runs/formal-v1'
    if run.exists():raise ValueError('Immutable run exists')
    run.mkdir(parents=True);start=time.monotonic()
    cases=batch.read(HERE/'runs/delayed-v1/cases.json');specs=ms.development_specs()
    paths=[Path(__file__),HERE/'FORMAL_PROTOCOL.md',HERE/'runs/delayed-v1/cases.json',ROOT/'paired_bank.py',ROOT/'fsm_ir.py',ROOT/'rtl_lab.py']
    batch.atomic(run/'plan.json',dict(kind='OFFLINE_RTL_BOUNDED_SAT',planned=5,seq_steps=14,timeout=30,new_model_calls=0,source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths},scope='Zero init, rst_n low at step1 high thereafter, each step an abstract clock tick; no analog or edge-between reset proof'))
    env=lab.run_process(['wsl','-d','Ubuntu','--','yosys','-V'],run,15);lab.save_process(run,'version',env)
    assert env['returncode']==0 and not env['timeout'];batch.atomic(run/'environment.json',dict(yosys_version=env['stdout']))
    results=[]
    for spec,case in zip(specs,cases):
        task=spec['id'];folder=run/task;folder.mkdir()
        good=bank.fixture_rtl(bank.graph(task),spec['ports'],'gold')
        bad=bank.fixture_rtl(fsm_ir.parse(ms.raw(case['ir'])),spec['ports'],'gate')
        r,b,q=(spec['ports'][k] for k in ('reset_port','input_port','output_port'))
        top=f'\nmodule miter(input clk,input rst_n,input din,output mismatch); wire g,a; gold G(.clk(clk),.{r}(rst_n),.{b}(din),.{q}(g)); gate A(.clk(clk),.{r}(rst_n),.{b}(din),.{q}(a)); assign mismatch=g^a; endmodule\n'
        lab.write_text(folder/'miter.v',good+'\n'+bad+top)
        constraints=' '.join(f'-set-at {i} rst_n {int(i>1)}' for i in range(1,15))
        ys='read_verilog miter.v\nhierarchy -top miter\nproc\nflatten\nopt\nasync2sync\nopt\nsat -seq 14 -set-init-zero '+constraints+' -prove mismatch 0 -show din -show rst_n -show mismatch -dump_json trace.json\n'
        lab.write_text(folder/'check.ys',ys)
        absolute=folder.resolve().as_posix();linux='/mnt/'+absolute[0].lower()+absolute[2:]
        result=lab.run_process(['wsl','-d','Ubuntu','--cd',linux,'--','yosys','-s','check.ys'],folder,30);lab.save_process(folder,'yosys',result)
        status='TIMEOUT' if result['timeout'] else 'TOOL_ERROR' if result['returncode']!=0 else 'COUNTEREXAMPLE_FOUND' if 'SAT proof finished - model found: FAIL!' in result['stdout'] else 'NO_COUNTEREXAMPLE_OR_UNPARSED'
        row=dict(task=task,status=status,elapsed_seconds=result['elapsed_seconds'],miter_sha256=lab.digest((folder/'miter.v').read_bytes()),trace_sha256=lab.digest((folder/'trace.json').read_bytes()) if (folder/'trace.json').exists() else None)
        results.append(row);batch.atomic(run/'results.json',results);print(task,status,flush=True)
        if status!='COUNTEREXAMPLE_FOUND':break
    batch.atomic(run/'summary.json',dict(kind='OFFLINE_RTL_BOUNDED_SAT',planned=5,completed=len(results),counterexamples=sum(r['status']=='COUNTEREXAMPLE_FOUND' for r in results),elapsed_seconds=time.monotonic()-start,model_calls=0,results=results,limits='14-step tick-level bounded check, forced reset, zero init, common deterministic compiler; not unbounded RTL equivalence.'))
    batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
if __name__=='__main__':main()
