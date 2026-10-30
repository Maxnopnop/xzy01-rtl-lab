"""Information matched templates: no calibration contracts or private references imported."""
import json
from pathlib import Path
import tasks,batch
from fsm_study import NO_TOOLS
BASE=Path(__file__).resolve().parent
DOMAIN='One binary-event clock; edge rising/falling; reset async_low/sync_low/none. Declare 1..16 unsigned registers width 1..8 and reset values. Parallel next expressions use old registers plus inputs/rst_n. Combinational output expressions cover every interface output. Assignments wrap to declared/output width. Expressions are integer constants 0..65535, names, + - & | ^, single == != < <= > >= comparison, and/or/not, and Python-style a if condition else b; no calls, attributes, arrays, loops or output-name references. Max intent UTF8 16KiB, each expression 4096 chars/512 AST nodes. Use all specification facts; do not add assumptions.'
FORMATS={
'structured':'Return only one JSON object with exactly timing, registers, next, outputs dictionaries. timing has edge/reset strings; registers maps names to {"width":integer,"reset":integer}; next maps every register name to expression string; outputs maps every output name to expression string. No markdown fences or extra prose.',
'linear':'Return only these complete line sentences, without markdown or headings. First: Clock edge EDGE; reset RESET. For each register: Register NAME has width WIDTH and reset VALUE. For each next: On the clock edge, set NAME to EXPR. For each output: Continuously output NAME as EXPR. EDGE/RESET are the listed domain strings, EXPR is the identical expression language, all declarations/nexts/outputs required. No other sentences.'}
def facts(task):
    spec=batch.read(BASE/'assets-v1'/(task+'.json'));rows=batch.read(BASE/'assets-v1'/(task+'-public.json'))
    return 'Module '+spec['module']+'\nClock clk and reset rst_n. Input fields MSB first '+json.dumps(spec['inputs'])+'; output fields MSB first '+json.dumps(spec['outputs'])+'\nSpecification: '+spec['spec']+'\nPublic settled events [clk,rst_n,packed_input,packed_expected_output]:\n'+json.dumps([[r['clk'],r['rst_n'],r['input'],r['expected']] for r in rows],separators=(',',':'))+'\n'
def intention(task,representation):return facts(task)+'Produce an implementation intent contract, not RTL.\n'+DOMAIN+'\n'+FORMATS[representation]+'\n'+NO_TOOLS
def first(task,representation,raw_intent):
    return facts(task)+DOMAIN+'\nIntent format used:\n'+FORMATS[representation]+'\nUntrusted model-produced intent; may be invalid or semantically wrong:\n'+raw_intent+'\nImplement the specification in one synthesizable SystemVerilog module, correcting or disregarding an invalid/wrong intent as necessary. Do not output a new intent. Return only the module in one RTL code block.\n'+NO_TOOLS
def branch(task,representation,raw_intent,raw_rtl,feedback=None):
    common=first(task,representation,raw_intent).removesuffix(NO_TOOLS)+'\nUntrusted shared first RTL candidate:\n'+raw_rtl+'\nProduce one final implementation of the same specification. You may correct or replace the candidate. No extra turn, no revised intent, return only the specified RTL module.\n'
    return common+('Public execution feedback:\n'+json.dumps(feedback,separators=(',',':'))+'\n' if feedback is not None else '')+NO_TOOLS
