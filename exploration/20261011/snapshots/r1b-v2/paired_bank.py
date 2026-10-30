"""Frozen paired-repair bank with independently specified behavioral oracles."""
import copy
import itertools
import json
from pathlib import Path
import random

import batch
import fsm_checks
import fsm_ir
import rtl_lab as lab

ROOT = batch.ROOT / 'benchmarks/paired-v1'
PORTS = dict(reset_port='rst_n', input_port='din', output_port='q', active=0)
DEVELOPMENT = ('sticky_alarm', 'event_parity', 'request_delay', 'debounce3')
HELDOUT = ('credit_bucket', 'framed_parity')


def graph(task):
    if task == 'rt_sequence':
        return fsm_checks.reference_ir(task)
    definitions = {
        'sticky_alarm': ([(0, 1), (0, 2), (2, 2)], [0, 0, 1]),
        'event_parity': ([(0, 1), (1, 0)], [0, 1]),
        'request_delay': ([(0, 1), (2, 2), (3, 3), (0, 3)], [0, 0, 1, 0]),
        'debounce3': ([(0, 1), (0, 2), (0, 3), (4, 3), (0, 3)], [0, 0, 0, 1, 1]),
        'credit_bucket': ([(0, 1), (0, 2), (1, 2)], [1, 0, 0]),
        # phase/parity states: start; bit1 even/odd; bit2 even/odd;
        # bit3 even/odd; completed frame even/odd.
        'framed_parity': ([(1, 2), (3, 4), (4, 3), (5, 6), (6, 5),
                           (7, 8), (8, 7), (1, 2), (1, 2)], [0, 0, 0, 0, 0, 0, 0, 1, 0])}
    edges, outputs = definitions[task]
    obj = dict(schema=1, clock_edge='posedge', output_kind='moore',
               reset=dict(kind='async', active=0, state='S0'),
               states=[dict(name=f'S{i}', output=q) for i, q in enumerate(outputs)],
               transitions=[{'from':f'S{i}', 'input':b, 'to':f'S{row[b]}'}
                            for i, row in enumerate(edges) for b in (0, 1)])
    return fsm_ir.parse(json.dumps(obj))


def oracle(task, inputs):
    """Procedural/history oracle independent of the reference FSM transition table."""
    q = None; history = ''; count = 0; latched = False; phase = 0; parity = 0; high = False; streak = 0
    rows = []
    for reset, bit in inputs:
        if not reset:
            history = ''; count = 0; latched = False; phase = 0; parity = 0; high = False; streak = 0
            q = int(task == 'credit_bucket')
        pre = q
        if reset:
            if task == 'rt_sequence':
                history = (history + str(bit))[-4:]; q = int(history == '1001')
            elif task == 'sticky_alarm':
                count = count + 1 if bit else 0; latched = latched or count >= 2; q = int(latched)
            elif task == 'event_parity':
                count += bit; q = count % 2
            elif task == 'request_delay':
                if phase == 0:
                    phase = 1 if bit else 0
                elif phase in (1, 2):
                    phase += 1
                elif not bit:
                    phase = 0
                q = int(phase == 2)
            elif task == 'debounce3':
                streak = streak + 1 if bool(bit) != high else 0
                if streak >= (2 if high else 3):
                    high = not high; streak = 0
                q = int(high)
            elif task == 'credit_bucket':
                count = min(2, count + 1) if bit else max(0, count - 1); q = int(count == 0)
            elif task == 'framed_parity':
                if phase == 4:
                    phase = 0; parity = 0
                phase += 1; parity ^= bit; q = int(phase == 4 and parity == 0)
            else:
                raise ValueError('Unknown behavioral oracle')
        rows.append((reset, bit, pre, q))
    return rows


DESCRIPTIONS = {
 'sticky_alarm': 'q starts at 0. Two consecutive sampled ones set q to 1. Once set, q remains 1 until reset, regardless of later input. A zero before activation breaks the consecutive-one count.',
 'event_parity': 'q starts at 0. On each rising clock edge with din=1, toggle q. With din=0 hold q. Thus q is the parity of the number of sampled ones since reset.',
 'request_delay': 'Initially idle with q=0. In idle, a sampled din=1 accepts a request. q remains 0 on that accepting edge, then is 1 for exactly the following clock cycle, regardless of din. At the next edge q returns to 0 and enters cooldown. In cooldown, remain there while din=1; an edge with din=0 returns to idle. The edge returning to idle does not accept a request.',
 'debounce3': 'Initially q=0. While q=0, require three consecutive sampled ones to change q to 1 on the third edge; any zero restarts this count. While q=1, require two consecutive sampled zeros to change q to 0 on the second edge; any one restarts this count. q otherwise holds.',
 'credit_bucket': 'Track credits with capacity two. Initially there are zero credits and q=1. At each rising edge, din=1 adds one credit, saturating at two; din=0 removes one credit, saturating at zero. q is 1 exactly when the current credit count is zero.',
 'framed_parity': 'Consume non-overlapping frames of four bits, one bit per rising edge. q is 0 for the first three edges of each frame. On the fourth edge q is 1 exactly when the four bits contain an even number of ones, else 0. The next edge starts the next frame and q returns to 0. Reset discards any incomplete frame.'}


def public_contract(task):
    if task == 'rt_sequence':
        return fsm_checks.public_contract(task)
    traces = {
      'sticky_alarm':['1011000','01010'], 'event_parity':['101101','000'],
      'request_delay':['11111001100','100000'], 'debounce3':['01110100111','110110'],
      'credit_bucket':['11100010','0101'], 'framed_parity':['000010011111','00010010']}
    return dict(clock_edge='posedge', output_kind='moore', reset=dict(kind='async', active=0, output=int(task=='credit_bucket')),
                trace_convention='Each trace starts after reset; output is sampled after every rising edge.',
                examples=[dict(bits=bits, outputs=[r[3] for r in oracle(task, [(0,0)]+[(1,int(b)) for b in bits])][1:]) for bits in traces[task]])


def feedback(raw, contract):
    try:
        ir = fsm_ir.parse(raw)
    except ValueError as exc:
        return dict(status='PUBLIC_CHECK_FAIL', errors=[str(exc)])
    errors = []
    for k in ('kind','active'):
        if ir['reset'][k] != contract['reset'][k]:
            errors.append(dict(field='reset.'+k, expected=contract['reset'][k], observed=ir['reset'][k]))
    expected = contract['reset']['output']; actual = ir['outputs'][ir['reset']['state']]
    if actual != expected:
        errors.append(dict(field='reset output', expected=expected, observed=actual))
    for case in contract['examples']:
        actual = fsm_ir.trace(ir, case['bits'])
        if actual != case['outputs']:
            errors.append(dict(bits=case['bits'], expected=case['outputs'], observed=actual))
    return dict(status='PUBLIC_CHECK_FAIL' if errors else 'PUBLIC_CHECK_PASS', errors=errors,
                scope='Only disclosed examples/reset/schema; private tests were not consulted.')


def fixture_rtl(ir, ports, module):
    names = list(ir['outputs']); ids = {s:i for i,s in enumerate(names)}
    r,b,q = (ports[k] for k in ('reset_port','input_port','output_port'))
    reset = ir['reset']; sense = 'posedge clk'
    if reset['kind'] == 'async': sense += f" or {'posedge' if reset['active'] else 'negedge'} {r}"
    cases = '\n'.join(f"{ids[s]}: state <= {b} ? {ids[ir['edges'][s,1]]} : {ids[ir['edges'][s,0]]};" for s in names)
    output = ' || '.join(f'(state=={ids[s]})' for s in names if ir['outputs'][s]) or "1'b0"
    return f'''module {module}(input clk, input {r}, input {b}, output {q});
reg [4:0] state;
always @({sense}) begin
if({r}==1'b{reset['active']}) state <= {ids[reset['state']]};
else case(state)
{cases}
default: state <= {ids[reset['state']]};
endcase
end
assign {q} = {output};
endmodule
'''


def input_schedule():
    # Exhaustive all words of length <=8, each reset-isolated; plus resets
    # within longer streams. Fixed across all tasks, independent of faults.
    inputs = []
    for length in range(1,9):
        for bits in itertools.product((0,1), repeat=length):
            inputs += [(0,0)] + [(1,b) for b in bits]
    rng = random.Random(20261001)
    inputs += [(0 if rng.randrange(19)==0 else 1, rng.randrange(2)) for _ in range(512)]
    return inputs


def mutate(ir, name):
    obj = copy.deepcopy(ir['data'])
    if name == 'sync_reset': obj['reset']['kind'] = 'sync'
    elif name == 'reset_polarity': obj['reset']['active'] ^= 1
    elif name == 'early_output':
        for s in obj['states']: s['output'] = int(s['name']=='S3')
    elif name == 'state_output':
        # Mutate a reachable non-reset state's output, preserving reset output.
        obj['states'][1]['output'] ^= 1
    elif name == 'transition':
        edge = next(e for e in obj['transitions'] if e['from']=='S0' and e['input']==1)
        edge['to'] = 'S0'
    else: raise ValueError('Unknown mutation')
    return json.dumps(obj, indent=2)+'\n'


def build():
    if ROOT.exists(): raise ValueError('Bank exists; never silently replace frozen tasks')
    ROOT.mkdir(parents=True); specs=[]; inputs=input_schedule(); cases=[]
    for task in ('rt_sequence',)+DEVELOPMENT+HELDOUT:
        reference=graph(task); ports=fsm_checks.CONTRACTS[task] if task=='rt_sequence' else PORTS
        module='sequence_detector' if task=='rt_sequence' else task
        if task=='rt_sequence':
            spec=copy.deepcopy(next(s for s in batch.manifest('dev10') if s['id']==task))
            directory=ROOT/task; directory.mkdir()
            source=batch.ROOT/batch.SUITES['dev10']
            (directory/'testbench.sv').write_bytes((source/(task+'_tb.sv')).read_bytes())
            for name in spec['assets']: (directory/name).write_bytes((source/name).read_bytes())
            task_inputs=fsm_checks.inputs_from_dev(source,spec)
        else:
            directory=ROOT/task; directory.mkdir(); task_inputs=inputs
            spec=dict(id=task,module=module,category='fsm',family=task,split='development' if task in DEVELOPMENT else 'heldout',
                      spec=f'Implement module {module}(input clk, input rst_n, input din, output q). Use rising clock edges, asynchronous active-low reset, and Moore outputs. '+DESCRIPTIONS[task])
            binding=fsm_checks.write_agreement_test(directory,spec,reference,inputs,ports)
            spec.update(checks=binding['checks'],tb_sha256=binding['tb_sha256'],assets={'agreement.hex':binding['vectors_sha256']})
        assert fsm_ir.timed_vectors(reference,task_inputs)==oracle(task,task_inputs), task
        spec.update(ports=ports,public_contract=public_contract(task),bank_directory=task)
        lab.write_text(directory/'reference.json',json.dumps(reference['data'],indent=2)+'\n')
        lab.write_text(directory/'reference.sv',fixture_rtl(reference,ports,module))
        lab.write_json(directory/'inputs.json',task_inputs)
        specs.append(spec)
    real=batch.ROOT/'evidence/fsm48/jobs/m02__rt_sequence__table__s001/stage1/response.txt'
    original=real.read_bytes(); (ROOT/'real_overlap.json').write_bytes(original)
    cases.append(dict(id='real_overlap',task='rt_sequence',stage='A',kind='REAL_RETAINED_IR',error_type='overlap_fallback',
                      ir_file='real_overlap.json',origin=str(real.relative_to(batch.ROOT)).replace('\\','/'),origin_sha256=lab.digest(original)))
    for mutation in ('sync_reset','reset_polarity','early_output'):
        name='rt_sequence_'+mutation; lab.write_text(ROOT/(name+'.json'),mutate(graph('rt_sequence'),mutation))
        cases.append(dict(id=name,task='rt_sequence',stage='A',kind='INJECTED_FAULT',error_type=mutation,ir_file=name+'.json'))
    for task in DEVELOPMENT:
        for mutation in ('transition','state_output'):
            name=task+'_'+mutation; lab.write_text(ROOT/(name+'.json'),mutate(graph(task),mutation))
            cases.append(dict(id=name,task=task,stage='B',kind='INJECTED_FAULT',error_type=mutation,ir_file=name+'.json'))
    for case in cases:
        raw=(ROOT/case['ir_file']).read_text(encoding='utf-8')
        diagnosis=fsm_ir.product_check(fsm_ir.parse(raw),graph(case['task']))
        assert diagnosis['status']=='IR_SPEC_MISMATCH', case['id']
        case['ir_sha256']=lab.digest((ROOT/case['ir_file']).read_bytes())
    batch.atomic(ROOT/'manifest.json',dict(schema=1,tasks=specs,cases=cases,
        split=dict(development=['rt_sequence',*DEVELOPMENT],heldout=list(HELDOUT)),
        note='Authored development stress bank, not an official benchmark. Held-out candidates receive offline oracle validation only.'))
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):lab.digest(p.read_bytes()) for p in ROOT.rglob('*') if p.is_file()}
    batch.atomic(ROOT/'bank-lock.json',hashes)
    print(f'Frozen bank: {len(specs)} tasks, {len(cases)} erroneous IRs, {len(inputs)} input cycles per new task')


def load():
    for name, expected in batch.read(ROOT/'bank-lock.json').items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT.resolve()) or lab.digest(path.read_bytes())!=expected:
            raise ValueError('Bank hash mismatch: '+name)
    return batch.read(ROOT/'manifest.json')


if __name__=='__main__': build()
