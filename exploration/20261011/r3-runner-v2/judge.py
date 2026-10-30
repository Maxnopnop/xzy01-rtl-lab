"""Bounded binary-event simulator; generated RTL is never Python code."""
import sys,re
from pathlib import Path
from types import SimpleNamespace
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT))
import batch,rtl_lab as lab,backends
from tasks import TASKS

def simulate(folder,task,raw,rows,tools=None):
    folder.mkdir(parents=True,exist_ok=True);spec=TASKS[task]
    try:dut=lab.extract_rtl(raw,spec['module'])
    except lab.LabError as exc:return dict(status=exc.status,stage=exc.stage,message=exc.message,mismatches=[])
    (folder/'dut.sv').write_bytes(dut.encode());iw=sum(w for n,w in spec['inputs']);ow=sum(w for n,w in spec['outputs']);width=iw+ow+2
    words=[f'{(((e["clk"]*2+e["rst_n"])<<iw)|e["input"])<<ow|e["expected"]:x}' for e in rows]
    (folder/'vectors.hex').write_bytes(('\n'.join(words)+'\n').encode())
    declarations=' '.join('reg '+(f'[{w-1}:0] ' if w>1 else '')+n+'=0;' for n,w in spec['inputs'])
    declarations+=' '.join('wire '+(f'[{w-1}:0] ' if w>1 else '')+n+';' for n,w in spec['outputs'])
    names=[n for n,w in spec['inputs']];outputs=[n for n,w in spec['outputs']]
    ports=', '.join('.'+n+'('+n+')' for n in ['clk','rst_n']+names+outputs)
    tb=f'''module tb;reg clk=0,rst_n=1;{declarations}
reg [{width-1}:0] vectors[0:{len(rows)-1}];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
{spec['module']} D({ports});
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<{len(rows)};i=i+1) begin {{clk,rst_n,{','.join(names)}}}=vectors[i][{width-1}:{ow}];#2;checks=checks+1;
if({{{','.join(outputs)}}} !== vectors[i][{ow-1}:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][{ow-1}:0],{{{','.join(outputs)}}});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
'''
    (folder/'testbench.sv').write_bytes(tb.encode());args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10)
    if tools is None:tools=lab.inspect_tools(args,folder)
    result=backends.IcarusBackend().evaluate(folder,dict(checks=len(rows)),tools,args)
    log=(folder/'simulate.stdout.log').read_text() if (folder/'simulate.stdout.log').exists() else ''
    result['mismatches']=[dict(event=int(i),expected=int(e),observed=o,category=rows[int(i)]['category']) for i,e,o in re.findall(r'MISMATCH event=(\d+) expected=(\d+) observed=([01xz]+)',log)]
    result.update(checks=len(rows),rtl_sha256=lab.digest((folder/'dut.sv').read_bytes()),tb_sha256=lab.digest(tb.encode()),vectors_sha256=lab.digest((folder/'vectors.hex').read_bytes()))
    return result

def public_feedback(task,raw,rows,folder,tools=None):
    # Only this explicitly passed public row set is accessible to the checker.
    result=simulate(folder,task,raw,rows,tools)
    return dict(status=result['status'],mismatches=result.get('mismatches',[]),scope='Disclosed examples and event checks only; no hidden stimuli/reference RTL',message=result.get('message'))
