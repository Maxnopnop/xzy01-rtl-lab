"""Public feedback and private diagnostics have explicitly separate entry points."""
import json
import re

import fsm_ir
import rtl_lab as lab


CONTRACTS = {
    've_fsm': dict(reset_port='areset', input_port='in', output_port='out', active=1,
                   examples=[dict(bits='1101', outputs=[0, 0, 0, 1]),
                             dict(bits='10101', outputs=[0, 0, 1, 0, 1])]),
    'rt_sequence': dict(reset_port='rst_n', input_port='data_in', output_port='sequence_detected', active=0,
                       examples=[dict(bits='1001', outputs=[0, 0, 0, 1]),
                                 dict(bits='1011', outputs=[0, 0, 0, 0]),
                                 dict(bits='1001001', outputs=[0, 0, 0, 1, 0, 0, 1])])}


def public_contract(task):
    c = CONTRACTS[task]
    return dict(clock_edge='posedge', output_kind='moore',
                reset=dict(kind='async', active=c['active'], output=0),
                trace_convention='Each trace starts after reset. List output after each rising edge; reset is then inactive.',
                examples=c['examples'])


def public_check(raw, task):
    """Only schema, specification metadata and already-disclosed examples."""
    try:
        ir = fsm_ir.parse(raw)
    except ValueError as exc:
        return dict(status='PUBLIC_CHECK_FAIL', errors=[str(exc)])
    c = public_contract(task); errors = []
    for key in ('kind', 'active'):
        if ir['reset'][key] != c['reset'][key]:
            errors.append(dict(field='reset.' + key, expected=c['reset'][key], observed=ir['reset'][key]))
    if ir['outputs'][ir['reset']['state']] != 0:
        errors.append(dict(field='reset output', expected=0, observed=ir['outputs'][ir['reset']['state']]))
    for case in c['examples']:
        observed = fsm_ir.trace(ir, case['bits'])
        if observed != case['outputs']:
            errors.append(dict(bits=case['bits'], expected=case['outputs'], observed=observed))
    return dict(status='PUBLIC_CHECK_FAIL' if errors else 'PUBLIC_CHECK_PASS', errors=errors,
                note='Only the public examples and schema were checked; passing is not full equivalence.')


def reference_ir(task):
    """Private oracle. Never include this graph or its diagnostics in prompts."""
    if task == 've_fsm':
        edges = ((0, 1), (2, 1), (0, 3), (2, 1)); accepting = 3
    elif task == 'rt_sequence':
        # Independent suffix/prefix construction for overlapping 1001.
        pattern = '1001'; edges = []
        for n in range(len(pattern) + 1):
            row = []
            for bit in '01':
                history = pattern[:n] + bit
                row.append(max(k for k in range(5) if history.endswith(pattern[:k])))
            edges.append(row)
        accepting = 4
    else:
        raise ValueError('Unknown FSM task')
    obj = dict(schema=1, clock_edge='posedge', output_kind='moore',
               reset=dict(kind='async', active=CONTRACTS[task]['active'], state='S0'),
               states=[dict(name=f'S{i}', output=int(i == accepting)) for i in range(len(edges))],
               transitions=[dict(**{'from': f'S{i}', 'input': bit, 'to': f'S{row[bit]}'})
                            for i, row in enumerate(edges) for bit in (0, 1)])
    return fsm_ir.parse(json.dumps(obj))


def private_check(raw, task):
    try:
        ir = fsm_ir.parse(raw)
    except ValueError as exc:
        return dict(status='IR_INVALID', error=str(exc))
    return fsm_ir.product_check(ir, reference_ir(task))


def inputs_from_dev(task_dir, spec):
    filename = spec['id'] + '.hex'; data = (task_dir / filename).read_bytes()
    if lab.digest(data) != spec['assets'][filename]:
        raise ValueError('Private stimulus hash changed')
    return [((int(v, 16) >> 4) & 1, (int(v, 16) >> 3) & 1) for v in data.decode().split()]


def write_agreement_test(folder, spec, ir, inputs):
    """Independent TB using the model's IR as oracle, on frozen private stimuli."""
    rows = fsm_ir.timed_vectors(ir, inputs); c = CONTRACTS[spec['id']]
    reset, bit, out = (c[k] for k in ('reset_port', 'input_port', 'output_port'))
    vectors = []; checks = 0
    for r, b, pre, post in rows:
        vp, vq = int(pre is not None), int(post is not None)
        checks += vp + vq
        word = (r << 5) | (b << 4) | ((pre or 0) << 3) | ((post or 0) << 2) | (vp << 1) | vq
        vectors.append(f'{word:02x}')
    lab.write_text(folder / 'agreement.hex', '\n'.join(vectors) + '\n')
    tb = f'''`timescale 1ns/1ps
module tb;
reg clk=0, {reset}, {bit}; wire {out};
reg pre, post, valid_pre, valid_post;
reg [5:0] vectors[0:{len(rows)-1}];
integer i, checks=0, errors=0, fd; reg [255:0] nonce;
{spec['module']} dut(.clk(clk), .{reset}({reset}), .{bit}({bit}), .{out}({out}));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("agreement.hex",vectors);
for(i=0;i<{len(rows)};i=i+1) begin
{{{reset},{bit},pre,post,valid_pre,valid_post}}=vectors[i]; #2;
if(valid_pre) begin checks=checks+1; if({out} !== pre) begin
errors=errors+1; if(errors<=5) $display("MISMATCH cycle=%0d phase=pre reset=%0d input=%0d expected=%0d observed=%0d",i,{reset},{bit},pre,{out}); end end
clk=1; #2;
if(valid_post) begin checks=checks+1; if({out} !== post) begin
errors=errors+1; if(errors<=5) $display("MISMATCH cycle=%0d phase=post reset=%0d input=%0d expected=%0d observed=%0d",i,{reset},{bit},post,{out}); end end
clk=0; #2;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
'''
    lab.write_text(folder / 'testbench.sv', tb)
    return dict(checks=checks, stimulus_count=len(rows),
                tb_sha256=lab.digest((folder / 'testbench.sv').read_bytes()),
                vectors_sha256=lab.digest((folder / 'agreement.hex').read_bytes()))


def mismatch_log(folder):
    path = folder / 'simulate.stdout.log'
    if not path.exists():
        return []
    pattern = r'MISMATCH cycle=(\d+) phase=(pre|post) reset=(\d) input=(\d) expected=(\d) observed=([01xz])'
    return [dict(cycle=int(i), phase=p, reset=int(r), input=int(b), expected=int(e), observed=o)
            for i, p, r, b, e, o in re.findall(pattern, path.read_text(encoding='utf-8'))]
