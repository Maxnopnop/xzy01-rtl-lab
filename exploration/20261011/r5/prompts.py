import json
from pathlib import Path
import tasks
BASE=Path(__file__).resolve().parent
def facts(task):
    t=tasks.TASKS[task];rows=json.loads((BASE/'assets'/f'{task}-public.json').read_text())
    return 'Implement module '+t['module']+' with clk,rst_n and ports '+json.dumps({k:t[k] for k in ('inputs','outputs')})+'\nSpecification:\n'+t['spec']+'\nPublic ordered binary events (clk,rst_n,packed input,packed output; ports packed in listed order; sample after #2):\n'+json.dumps(rows,separators=(',',':'))
def intention(task):return facts(task)+'\nReturn ONLY one executable JSON intention, no fences. Schema: timing:{reset:async_low|sync_low|none}, registers:{name:{width:1..8,reset:int}}, next_rising:{name:expression}, next_falling:{name:expression}, outputs:{port:expression}. Each register belongs to exactly one next bank; union covers all. Max16 registers,16KiB. Expressions: inputs/rst_n/register names, int0..65535, + - & | ^, << >> constant0..7, single comparisons, and/or/not, a if condition else b; no calls or arrays. Parallel old-state update on declared edge, assignment wraps to width, outputs continuous. Max4096 chars/512 AST nodes per expression.'
def first(task,rep,ir):return facts(task)+'\nExecutable intention from preceding stage (untrusted, may be wrong):\n'+ir+'\nReturn only complete synthesizable Verilog RTL, one module or one code block, no tb, delays/tools. Use specification as authority.'
def direct(task):return facts(task)+'\nReturn only complete synthesizable Verilog RTL, one module or one code block, no tb, delays/tools.'
def second(task,candidate):return facts(task)+'\nEarlier RTL (untrusted):\n'+candidate+'\nIndependently reconsider the full specification and generate a complete improved RTL. No execution results are supplied. Return only RTL; no tools/tb/delays.'
def branch(task,rep,ir,candidate,feedback):
    # Identical final stage info for S/D: no explicit IR or IR diagnostic supplied.
    p=facts(task)+'\nParent RTL (untrusted):\n'+candidate+'\nReconsider all timing, priority, reset and hold requirements and produce complete RTL. Return only RTL; no tools/tb/delays.'
    if feedback is not None:p+='\nPublic RTL versus SPEC execution result:\n'+json.dumps(feedback,separators=(',',':'))
    return p
