"""Rebuild audited dev10-v1 from vendored MIT sources; deterministic independent oracles."""
import hashlib
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parent/'benchmarks/dev10'
VE = ('verilog-eval','https://github.com/NVlabs/verilog-eval','c498220d0a52248f8e3fdffe279075215bde2da6')
RT = ('RTLLM','https://github.com/hkust-zhiyao/RTLLM','51ed553d0ffd32797a1a0a13e051656bf302c81f')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,text): path.write_bytes(text.encode('utf-8'))
def dump(path,obj): write(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def build():
    for name in ('tasks','reference','mutants'):(ROOT/name).mkdir(parents=True,exist_ok=True)
    manifest=[]
    rng=random.Random(20260930)

    def add(ident,origin,key,category,family,inputs,outputs,vectors,sequential,mutation,note=''):
        source=ROOT/'upstream'/origin[0]
        if origin==VE:
            prompt=source/(key+'_prompt.txt');ref=source/(key+'_ref.sv');tb=source/(key+'_test.sv')
            top='TopModule';sourcepath='dataset_spec-to-rtl/'+key
        else:
            source=source/key;prompt=source/'design_description.txt';ref=next(source.glob('verified*'));tb=source/'testbench.v'
            top=key
            sourcepath={'comparator_3bit':'Arithmetic/Comparator','counter_12':'Control/Counter',
                        'sequence_detector':'Control/Finite State Machine','right_shifter':'Memory/Shifter',
                        'multi_pipe_4bit':'Arithmetic/Multiplier'}[key]+'/'+key
        code=ref.read_text(encoding='utf-8-sig')
        code=re.sub(r'^\s*`timescale[^\n]*\n','',code,flags=re.M)
        code=re.sub(r'\bmodule\s+\w+', 'module '+top,code,count=1).strip()+'\n'
        write(ROOT/'reference'/(ident+'.sv'),code)
        old,new,label=mutation
        if old not in code:raise ValueError('Mutation target missing: '+ident)
        mutant=code.replace(old,new,1)
        write(ROOT/'mutants'/(ident+'.sv'),mutant)
        ni=sum(width for _,width in inputs);no=sum(width for _,width in outputs)
        width=ni+no*(2 if sequential else 1)+(1 if sequential else 0)
        lines=[]
        for values in vectors:
            if sequential:
                inp,pre,post,valid=values
                n=(inp << (2*no+1)) | (pre << (no+1)) | (post<<1) | valid
            else:
                inp,expected=values;n=(inp<<no)|expected
            lines.append(f'{n:0{(width+3)//4}x}')
        vec=ident+'.hex';write(ROOT/'tasks'/vec,'\n'.join(lines)+'\n')
        decl=lambda ports,typ:'\n'.join(f'{typ} '+(f'[{w-1}:0] ' if w>1 else '')+name+';' for name,w in ports)
        ins='{'+','.join(name for name,_ in inputs)+'}'
        outs='{'+','.join(name for name,_ in outputs)+'}'
        wiring=', '.join('.'+n+'('+n+')' for n,_ in inputs+outputs)
        if sequential:wiring='.clk(clk), '+wiring
        checks=len(vectors)+sum(v[3] for v in vectors) if sequential else len(vectors)
        step=(f'{{{ins}, expected_pre, expected, valid_pre}}=vectors[i]; #2;\n'
              f'if(valid_pre) begin checks=checks+1; if({outs} !== expected_pre) errors=errors+1; end\n'
              f'clk=1; #2; checks=checks+1; if({outs} !== expected) errors=errors+1; clk=0; #2;') if sequential else (
              f'{{{ins}, expected}}=vectors[i]; #2; checks=checks+1; if({outs} !== expected) errors=errors+1;')
        bench=f'''// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
{decl(inputs,'reg')}
{decl(outputs,'wire')}
{'reg clk=0; reg valid_pre; reg ['+str(no-1)+':0] expected_pre;' if sequential else ''}
reg [{no-1}:0] expected;
reg [{width-1}:0] vectors[0:{len(vectors)-1}];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
{top} dut({wiring});
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("{vec}",vectors);
for(i=0;i<{len(vectors)};i=i+1) begin
{step}
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
'''
        tbpath=ROOT/'tasks'/(ident+'_tb.sv');write(tbpath,bench)
        spec=prompt.read_text(encoding='utf-8-sig').strip()
        if note:spec+='\n\nDevelopment-subset clarification (part of the fixed specification): '+note
        entry=dict(id=ident,module=top,checks=checks,spec=spec,category=category,split='development',
            family=family,benchmark=origin[0],suite_version='dev10-v1',synthesis_eligible=True,
            origin=dict(repository=origin[1],commit=origin[2],path=sourcepath,license='MIT',
                        files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (prompt,ref,tb)}),
            adaptations=['Independent deterministic vector oracle replaces upstream TB; upstream TB archived.',
                         'Reference module renamed; timescale directive removed.']+([note] if note else []),
            mutation=label,reference_sha256=sha(ROOT/'reference'/(ident+'.sv')),
            mutant_sha256=sha(ROOT/'mutants'/(ident+'.sv')),tb_sha256=sha(tbpath),assets={vec:sha(ROOT/'tasks'/vec)})
        manifest.append(entry)

    # Combinational arithmetic: exhaustive two 8-bit operands and both operations.
    v=[((s<<16)|(a<<8)|b, (((a-b if s else a+b)&255)<<1)|int(((a-b if s else a+b)&255)==0))
       for s in range(2) for a in range(256) for b in range(256)]
    add('ve_addsub',VE,'Prob123_bugs_addsubz','arithmetic','addsub', [('do_sub',1),('a',8),('b',8)],
        [('out',8),('result_is_zero',1)],v,False,('out == 0','out != 0','Incorrect zero flag'))
    mask=(1<<255)-1
    values=[0,mask]+[1<<i for i in range(255)]+[mask^(1<<i) for i in range(255)]+[rng.getrandbits(255) for _ in range(600)]
    add('ve_popcount',VE,'Prob030_popcount255','arithmetic','popcount',[('in',255)],[('out',8)],
        [(n,n.bit_count()) for n in values],False,('i<255','i<254','Drops most significant input bit'))
    q=0;v=[]
    for i in range(320):
        reset=int(i==0 or i%23==9);pre=q;q=0 if reset or q==9 else q+1
        v.append((reset,pre,q,int(i>0)))
    add('ve_count10',VE,'Prob040_count10','sequential','counter',[('reset',1)],[('q',4)],v,True,
        ('q == 9','q == 8','Wrong counter wrap'))
    q=0;v=[];mask=(1<<100)-1
    for i in range(420):
        load=int(i==0 or i%17==0);ena=i%4;data=rng.getrandbits(100);pre=q
        if load:q=data
        elif ena==1:q=(q>>1)|((q&1)<<99)
        elif ena==2:q=((q<<1)&mask)|(q>>99)
        v.append(((load<<102)|(ena<<100)|data,pre,q,int(i>0)))
    add('ve_rotate',VE,'Prob105_rotate100','sequential','rotate',[('load',1),('ena',2),('data',100)],[('q',100)],v,True,
        ('{q[0], q[99:1]}','{q[98:0], q[99]}','Wrong rotate direction'))
    state=0;v=[];trans=((0,1),(2,1),(0,3),(2,1))
    for i in range(800):
        reset=int(i==0 or i%29==7);bit=rng.randrange(2)
        if reset:state=0
        pre=int(state==3);state=0 if reset else trans[state][bit]
        v.append(((reset<<1)|bit,pre,int(state==3),1))
    add('ve_fsm',VE,'Prob119_fsm3','fsm','fsm3',[('areset',1),('in',1)],[('out',1)],v,True,
        ('state==D','state==C','Wrong Moore output state'))
    add('rt_comparator',RT,'comparator_3bit','combinational','comparator',[('A',3),('B',3)],
        [('A_greater',1),('A_equal',1),('A_less',1)],
        [((a<<3)|b, (int(a>b)<<2)|(int(a==b)<<1)|int(a<b)) for a in range(8) for b in range(8)],False,
        ('A > B','$signed(A) > $signed(B)','Signed instead of unsigned comparison'))
    q=0;v=[]
    for i in range(480):
        rst=int(not(i==0 or i%37==8));en=int(i%5!=2)
        if not rst:q=0
        pre=q
        if rst and en:q=(q+1)%12
        v.append(((rst<<1)|en,pre,q,1))
    add('rt_counter12',RT,'counter_12','sequential','counter',[('rst_n',1),('valid_count',1)],[('out',4)],v,True,
        ("out == 4'd11","out == 4'd10",'Wrong counter wrap'),
        'rst_n is asynchronous active-low; counting is on rising clk edges, matching the archived reference.')
    # Independent sliding-window oracle checks overlapping 1001 detection.
    history=[];v=[];prev=0
    bits=[int(c) for c in '10010011001100100100011001']*20+[rng.randrange(2) for _ in range(400)]
    for i,bit in enumerate(bits):
        rst=int(not(i==0 or i%97==33))
        if not rst:history=[];prev=0
        pre=prev
        if rst:history=(history+[bit])[-4:]
        prev=int(history==[1,0,0,1])
        v.append(((rst<<1)|bit,pre,prev,1))
    add('rt_sequence',RT,'sequence_detector','fsm','sequence1001',[('rst_n',1),('data_in',1)],[('sequence_detected',1)],v,True,
        ('data_in?S1:S2;', 'data_in?S1:IDLE;', 'Breaks sequence prefix transition'),
        'Use asynchronous active-low reset, overlapping detections, and a Moore output high after the edge consuming the final 1; matching the archived reference.')
    q=0;v=[]
    for i in range(640):
        bit=(i//3)%2 if i<160 else rng.randrange(2);pre=q;q=(q>>1)|(bit<<7);v.append((bit,pre,q,1))
    add('rt_shift',RT,'right_shifter','sequential','shiftregister',[('d',1)],[('q',8)],v,True,
        ('q >> 1','q << 1','Wrong shift direction'),
        'Output q is 8 bits. The specified initial q=0 is required; this generic synthesis check retains initialization and makes no ASIC power-up guarantee.')
    partial=out=0;v=[]
    pairs=[(a,b) for a in range(16) for b in range(16)]+[(rng.randrange(16),rng.randrange(16)) for _ in range(256)]
    for i,(a,b) in enumerate(pairs):
        rst=int(not(i==0 or i%71==12))
        if not rst:partial=out=0
        pre=out
        if rst:out,partial=partial,a*b
        v.append(((rst<<8)|(a<<4)|b,pre,out,1))
    add('rt_pipeline',RT,'multi_pipe_4bit','pipeline','multiplier',[('rst_n',1),('mul_a',4),('mul_b',4)],[('mul_out',8)],v,True,
        ('mul_result[2] + mul_result[3]','mul_result[2]', 'Drops high partial product'),
        'Evaluate only size=4. Keep parameter size=4 and the specified port widths. The output after an edge equals the product of inputs sampled one rising edge earlier (two register stages).')
    dump(ROOT/'tasks/manifest.json',manifest)
    sources={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted((ROOT/'upstream').rglob('*'),key=lambda p:p.relative_to(ROOT).as_posix()) if p.is_file()}
    dump(ROOT/'source-lock.json',dict(version='dev10-v1',sources=sources,repositories=[dict(name=o[0],url=o[1],commit=o[2],license='MIT') for o in (VE,RT)]))
    dump(ROOT/'split-lock.json',dict(version='dev10-v1',development=[s['id'] for s in manifest],final=[],
        reserved_from_final_families=sorted({s['family'] for s in manifest}),
        policy='All variants/near duplicates of these dev families must stay out of final. Final 40 tasks not yet selected or audited. No final scores.'))
    print('Built',len(manifest),'audited development tasks;',sum(s['checks'] for s in manifest),'checks')


if __name__=='__main__':build()
