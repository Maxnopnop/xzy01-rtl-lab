"""New supplemental templates only; never rewrite or execute original tests."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def text(name,value):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value.encode())
def write(name,value):text(name,json.dumps(value,indent=2)+'\n')
def main():
    assert not (HERE/'supplemental').exists()
    mux='Prob018_mux256to1';fsm='Prob095_review2015_fsmshift'
    miters={
      mux:'module miter(input [255:0] in,input [7:0] sel,output mismatch); wire g,d; RefModule gold(.in(in),.sel(sel),.out(g)); TopModule candidate(.in(in),.sel(sel),.out(d)); assign mismatch=g^d; endmodule\n',
      fsm:'module miter(input clk,input reset,output mismatch); wire g,d; RefModule gold(.clk(clk),.reset(reset),.shift_ena(g)); TopModule candidate(.clk(clk),.reset(reset),.shift_ena(d)); assign mismatch=g^d; endmodule\n'}
    for task,miter in miters.items():
        text(f'supplemental/{task}/miter.sv',miter)
        for bound in (14,32):
            constraint=' -set-at 1 reset 1 -prove-skip 1' if task==fsm else ''
            ys=('read_verilog -sv reference.sv dut.sv miter.sv\nhierarchy -top miter\nproc\nflatten\nopt\n'
                f'sat -seq {bound} -set-def-inputs{constraint} -prove mismatch 0 -show-inputs -show-outputs -dump_json trace.json\n')
            text(f'supplemental/{task}/check-{bound}.ys',ys)
    sequence=[(0,0,'initial_unknown'),(0,1,'reset_assert_no_edge'),(1,1,'first_reset_edge'),
        (1,0,'release_high'),(0,0,'fall_hold'),(1,0,'active_1'),(0,0,'fall_hold'),
        (1,0,'active_2'),(0,0,'fall_hold'),(1,0,'active_3'),(0,0,'fall_hold'),
        (1,0,'done_4'),(1,1,'pulse_no_edge'),(1,0,'pulse_end_no_edge'),(0,0,'fall_hold'),
        (1,0,'done_stays'),(0,1,'reset_low_phase'),(1,1,'restart_edge'),(0,1,'held_reset_fall'),
        (1,1,'held_reset_edge'),(1,0,'release_high'),(0,0,'fall_hold'),(1,0,'active_1'),
        (0,0,'fall_hold'),(1,0,'active_2'),(0,0,'fall_hold'),(1,0,'active_3'),
        (0,0,'fall_hold'),(1,0,'done_4'),(0,0,'done_fall'),(1,0,'done_stays')]
    rows=[];remaining=None;last=0
    for i,(clk,reset,category) in enumerate(sequence):
        if clk and not last:
            if reset:remaining=4
            elif remaining is not None:remaining=max(0,remaining-1)
        q=None if remaining is None else int(remaining>0)
        rows.append(dict(index=i,drive_time=i*4,sample_time=i*4+1,clk=clk,reset=reset,
                         expected=q,score=q is not None,category=category))
        last=clk
    # Hand boundary witnesses, not DUT results.
    assert [rows[i]['expected'] for i in (2,5,7,9,11)]==[1,1,1,1,0]
    assert [rows[i]['expected'] for i in (12,13,15,16,17,19,28)]==[0,0,0,0,1,1,0]
    write(f'supplemental/{fsm}/diagnostic-events.json',rows)
    tb=['module tb; reg clk=0,reset=0; wire shift_ena; integer errors=0,checks=0;',
        'TopModule dut(.clk(clk),.reset(reset),.shift_ena(shift_ena));','initial begin']
    elapsed=0
    for r in rows:
        tb.append(f'#{r["drive_time"]-elapsed}; clk={r["clk"]}; reset={r["reset"]}; #1;')
        if r['score']:tb.append(f'checks=checks+1; if(shift_ena !== 1\'b{r["expected"]}) begin errors=errors+1; $display("EVENT_FAIL index={r["index"]}"); end')
        elapsed=r['sample_time']
    tb+=['$display("PUBLIC_DIAGNOSTIC checks=%0d errors=%0d",checks,errors); $finish; end endmodule']
    text(f'supplemental/{fsm}/diagnostic-testbench.sv','\n'.join(tb)+'\n')
    write('supplemental/coverage.json',{
        'status':'DESIGN_ONLY_NOT_COMPILED_OR_CALIBRATED','tasks':{
          mux:{'sat14_32':'PLANNED_UNVALIDATED; combinational selection, no init/reset/clock constraints, repeated steps not temporal proof',
            'reset_events':'NOT_APPLICABLE_COMBINATIONAL','reference':'Original upstream RefModule, correlated; no independent author claim'},
          fsm:{'sat14_32':'PLANNED_UNVALIDATED; synchronous active-high reset at abstract step1, skip first observation; subsequent reset unconstrained. No zero-init or async2sync.',
            'events':'31 separately authored diagnostic events, 29 scored after first reset, sampling drive+1; no original TB/vector changed',
            'temporal_interpretation':'reset edge starts first of four enabled intervals; held reset restarts; terminal output0 until sampled reset',
            'reference':'SAT same upstream RefModule; event expected values from independently written countdown rule by same project author, not external independent validation'}},
        'limits':'Cannot claim added findings, suitability of SAT flags, original-input equivalence or runtime correctness until separately reviewed offline validation. No old90972 events or old low-active/zero-init assumptions reused.'})
    print(json.dumps({'formal_templates':4,'event_rows':len(rows),'scored':sum(r['score'] for r in rows),'eda_calls':0}))
if __name__=='__main__':main()
