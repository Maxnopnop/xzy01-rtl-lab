"""Build reviewed, deterministic local tasks. Not a public benchmark."""
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build():
    manifest = json.loads((ROOT / 'tasks/manifest.json').read_text())[:3]
    for spec in manifest:
        spec['category'] = 'sequential' if spec['id'] == 'counter4' else 'combinational'
        spec['origin'] = 'local_handwritten_v1'
    rng = random.Random(20260930)

    def add(name, ports, behavior, inputs, outputs, vectors, gold, wrong, sequential=False):
        iw, ow = sum(w for _, w in inputs), sum(w for _, w in outputs)
        n = len(vectors)
        width = iw + ow
        data = ''.join(f'{(x << ow) | y:0{(width + 3)//4}x}\n' for x, y in vectors).encode()
        asset = name + '_vectors.hex'
        (ROOT / 'tasks' / asset).write_bytes(data)
        declarations = '\n'.join(f'  reg [{w-1}:0] {p};' for p, w in inputs)
        declarations += '\n' + '\n'.join(f'  wire [{w-1}:0] {p};' for p, w in outputs)
        in_concat = '{' + ', '.join(p for p, _ in inputs) + '}'
        out_concat = '{' + ', '.join(p for p, _ in outputs) + '}'
        connections = ', '.join(f'.{p}({p})' for p, _ in inputs + outputs)
        if sequential:
            declarations += '\n  reg clk = 0;'
            connections = '.clk(clk), ' + connections
        drive = f'{in_concat} = vectors[i][{width-1}:{ow}];'
        if sequential:
            step = f'''#2; {drive}
      #1; if (i > 0) check_value(previous);
      clk = 1; #1; check_value(vectors[i][{ow-1}:0]);
      previous = vectors[i][{ow-1}:0]; #1; clk = 0;'''
        else:
            step = f'{drive} #1; check_value(vectors[i][{ow-1}:0]);'
        tb = f'''`timescale 1ns/1ps
module tb;
{declarations}
  {name} dut({connections});
  reg [{width-1}:0] vectors [0:{n-1}];
  reg [{ow-1}:0] previous;
  reg [255:0] nonce;
  integer checks = 0, errors = 0, i, fd;
  task check_value(input [{ow-1}:0] expected);
    begin
      checks = checks + 1;
      if ({out_concat} !== expected) begin
        errors = errors + 1;
        if (errors <= 8) $display("Mismatch vector=%0d got=%h want=%h", i, {out_concat}, expected);
      end
    end
  endtask
  initial begin
    $readmemh("{asset}", vectors);
    for (i = 0; i < {n}; i = i + 1) begin
      {step}
    end
    if (!$value$plusargs("nonce=%s", nonce)) $fatal(1, "Missing nonce");
    fd = $fopen("verdict.txt", "w");
    if (fd == 0) $fatal(1, "Cannot write receipt");
    $fdisplay(fd, "RTL_LAB_V1 %0s checks=%0d errors=%0d", nonce, checks, errors);
    $fclose(fd);
    if (errors != 0) $fatal(1, "Functional mismatches: %0d", errors);
    $finish;
  end
endmodule
'''
        tb_bytes = tb.encode()
        (ROOT / 'tasks' / (name + '_tb.sv')).write_bytes(tb_bytes)
        for folder, code in [('correct', gold), ('wrong', wrong)]:
            (ROOT / 'examples' / folder / (name + '.sv')).write_text(f'module {name}({ports});\n{code}\nendmodule\n', encoding='utf-8')
        manifest.append(dict(id=name, module=name, category='sequential' if sequential else 'combinational',
            origin='local_handwritten_v2', spec=f'Implement module {name}({ports}). {behavior}',
            checks=2*n-1 if sequential else n, tb_sha256=sha(tb_bytes),
            assets={asset: sha(data)}, vectors=n))

    def comb(name, ports, behavior, ins, outs, cases, ref, code, wrong):
        vectors = []
        for values in cases:
            packed = 0
            for v, (_, w) in zip(values, ins):
                packed = (packed << w) | v
            vectors.append((packed, ref(*values)))
        add(name, ports, behavior, ins, outs, vectors, code, wrong)

    pairs = [(a, b) for a in range(256) for b in (0, 1, 127, 128, 254, 255)]
    pairs += [(rng.randrange(256), rng.randrange(256)) for _ in range(1024)]
    comb('mux8', 'input wire [7:0] a, b, input wire sel, output wire [7:0] y',
         'Combinational: y=a when sel=0, otherwise y=b.', [('a',8),('b',8),('sel',1)], [('y',8)],
         [(a,b,s) for a,b in pairs for s in range(2)], lambda a,b,s: b if s else a,
         'assign y = sel ? b : a;', 'assign y = sel ? a : b;')
    comb('alu8', 'input wire [7:0] a, b, input wire [2:0] op, output reg [7:0] y',
         'Combinational unsigned 8-bit ALU. op 0:add modulo 256; 1:a-b modulo 256; 2:AND; 3:OR; 4:XOR; 5:a<<1 modulo 256; 6:a>>1 logical; 7:unsigned a<b (8-bit 0 or 1).',
         [('a',8),('b',8),('op',3)],[('y',8)],[(a,b,o) for a,b in pairs for o in range(8)],
         lambda a,b,o: [a+b,a-b,a&b,a|b,a^b,a<<1,a>>1,int(a<b)][o]&255,
         'always @* case(op) 0:y=a+b; 1:y=a-b; 2:y=a&b; 3:y=a|b; 4:y=a^b; 5:y=a<<1; 6:y=a>>1; 7:y=(a<b); endcase',
         'always @* y=a+b;')
    comb('shift8','input wire [7:0] a, input wire [2:0] amount, input wire right, output wire [7:0] y',
         'Combinational logical shift. right=1: a>>amount; right=0: a<<amount. Zero fill; truncate to 8 bits.',
         [('a',8),('amount',3),('right',1)],[('y',8)],[(a,n,r) for a in range(256) for n in range(8) for r in range(2)],
         lambda a,n,r: (a>>n if r else a<<n)&255,'assign y=right ? a>>amount : a<<amount;', 'assign y=a<<amount;')
    comb('signedcmp8','input wire signed [7:0] a, b, output wire lt, eq, gt',
         'Combinational two\'s-complement signed comparison: lt=(a<b), eq=(a==b), gt=(a>b).',
         [('a',8),('b',8)],[('lt',1),('eq',1),('gt',1)],pairs,
         lambda a,b: (int((a^128)<(b^128))<<2)|(int(a==b)<<1)|int((a^128)>(b^128)),
         'assign lt=a<b; assign eq=a==b; assign gt=a>b;', 'assign lt=$unsigned(a)<$unsigned(b); assign eq=a==b; assign gt=$unsigned(a)>$unsigned(b);')
    comb('popcount8','input wire [7:0] a, output reg [3:0] count','Combinational population count: number of 1 bits in a, from 0 through 8.',
         [('a',8)],[('count',4)],[(a,) for a in range(256)],lambda a: bin(a).count('1'),
         'integer i; always @* begin count=0; for(i=0;i<8;i=i+1) count=count+a[i]; end',
         'integer i; always @* begin count=0; for(i=0;i<7;i=i+1) count=count+a[i]; end')
    comb('decoder3','input wire [2:0] index, input wire en, output wire [7:0] y','Combinational 3-to-8 one-hot decoder: en=0 gives 0; otherwise bit index is 1 and other bits are 0.',
         [('index',3),('en',1)],[('y',8)],[(i,e) for i in range(8) for e in range(2)],lambda i,e: (1<<i) if e else 0,
         "assign y=en ? (8'b1<<index) : 8'b0;", "assign y=8'b1<<index;")
    comb('gray8','input wire [7:0] binary, output wire [7:0] gray','Combinational binary to reflected Gray code conversion: gray=binary XOR (binary>>1).',
         [('binary',8)],[('gray',8)],[(a,) for a in range(256)],lambda a:a^(a>>1),
         'assign gray=binary^(binary>>1);','assign gray=binary^(binary<<1);')
    comb('parity8','input wire [7:0] a, output wire parity','Combinational parity equals 1 exactly when a contains an odd number of 1 bits.',
         [('a',8)],[('parity',1)],[(a,) for a in range(256)],lambda a:bin(a).count('1')%2,
         'assign parity=^a;','assign parity=~^a;')
    comb('saturating8','input wire [7:0] a, b, output wire [7:0] y','Combinational unsigned saturating sum: min(a+b,255), retaining the carry for saturation.',
         [('a',8),('b',8)],[('y',8)],pairs,lambda a,b:min(a+b,255),
         "wire [8:0] s; assign s={1'b0,a}+{1'b0,b}; assign y=s[8] ? 8'hff : s[7:0];", 'assign y=a+b;')
    comb('leadingzero8','input wire [7:0] a, output reg [3:0] count','Combinational count of consecutive zeros from bit 7 toward bit 0, before the first 1; count=8 when a=0.',
         [('a',8)],[('count',4)],[(a,) for a in range(256)],lambda a:8-a.bit_length(),
         'integer i; reg seen; always @* begin count=0; seen=0; for(i=7;i>=0;i=i-1) begin if(a[i]) seen=1; if(!seen) count=count+1; end end',
         'always @* count=0;')

    def seq(name, ports, behavior, ins, outs, stimuli, transition, initial, gold, wrong):
        state = initial
        vectors=[]
        for values in stimuli:
            state, output = transition(state,*values)
            x=0
            for v,(_,w) in zip(values,ins): x=(x<<w)|v
            vectors.append((x,output))
        add(name,ports,behavior,ins,outs,vectors,gold,wrong,True)

    sync='All state changes only on rising clk. rst is active-high synchronous and has priority. State before the first reset edge is unspecified. '
    stim=[(1,0,0),(0,1,255),(0,0,0),(1,1,42)]+[(int(i%31==0),rng.randrange(2),rng.randrange(256)) for i in range(256)]
    seq('dff8','input wire clk, rst, en, input wire [7:0] d, output reg [7:0] q',sync+'On rst set q=0; else if en set q=d; else hold.',
        [('rst',1),('en',1),('d',8)],[('q',8)],stim,lambda s,r,e,d: ((0 if r else d if e else s),)*2,0,
        'always @(posedge clk) if(rst) q<=0; else if(en) q<=d;', 'always @(posedge clk or posedge rst) if(rst) q<=0; else if(en) q<=d;')
    stim=[(1,0,0)]+[(0,1,1)]*12+[(int(i%29==0),rng.randrange(2),rng.randrange(2)) for i in range(256)]
    seq('shiftreg8','input wire clk, rst, en, serial_in, output reg [7:0] q',sync+'On rst q=0; else if en q={q[6:0],serial_in}; else hold.',
        [('rst',1),('en',1),('serial_in',1)],[('q',8)],stim,lambda s,r,e,d: ((0 if r else ((s<<1)|d)&255 if e else s),)*2,0,
        'always @(posedge clk) if(rst) q<=0; else if(en) q<={q[6:0],serial_in};',
        'always @(posedge clk) if(rst) q<=0; else if(en) q<={serial_in,q[7:1]};')
    stim=[(1,0,0),(0,1,0),(0,1,1)]+[(0,1,1)]*260+[(int(i%47==0),rng.randrange(2),rng.randrange(2)) for i in range(256)]
    seq('updown8','input wire clk, rst, en, up, output reg [7:0] q',sync+'On rst q=0; else if en, add 1 when up=1 or subtract 1 when up=0, modulo 256; else hold.',
        [('rst',1),('en',1),('up',1)],[('q',8)],stim,lambda s,r,e,u:((0 if r else (s+(1 if u else -1))&255 if e else s),)*2,0,
        'always @(posedge clk) if(rst) q<=0; else if(en) if(up) q<=q+1; else q<=q-1;',
        'always @(posedge clk) if(rst) q<=0; else if(en) q<=q+1;')
    def edge(s,r,d):
        return ((0,0),0) if r else ((d,int(d and not s[0])),int(d and not s[0]))
    stim=[(1,0),(0,1),(0,1),(0,0),(0,1)]+[(int(i%37==0),rng.randrange(2)) for i in range(256)]
    seq('edge_detector','input wire clk, rst, din, output reg pulse',sync+'Register din history and output pulse. On rst both history and pulse=0. Otherwise pulse is 1 for this cycle iff current sampled din=1 and previous sampled din=0. Update history each rising edge.',
        [('rst',1),('din',1)],[('pulse',1)],stim,edge,(0,0),
        'reg prev; always @(posedge clk) if(rst) begin prev<=0; pulse<=0; end else begin pulse<=din & ~prev; prev<=din; end',
        'always @(posedge clk) if(rst) pulse<=0; else pulse<=din;')
    def div(s,r,e):
        if r:return (0,0),0
        c=(s[0]+1)%4 if e else s[0]
        p=int(e and s[0]==3)
        return (c,p),p
    stim=[(1,0)]+[(0,1)]*16+[(int(i%41==0),rng.randrange(2)) for i in range(256)]
    seq('pulse_div4','input wire clk, rst, en, output reg pulse',sync+'Internal counter initially 0 on reset. Each enabled edge increments modulo 4. pulse=1 on an enabled edge whose old counter was 3, otherwise pulse=0 (including disabled edges). Disabled edges hold counter, not pulse.',
        [('rst',1),('en',1)],[('pulse',1)],stim,div,(0,0),
        'reg [1:0] count; always @(posedge clk) if(rst) begin count<=0; pulse<=0; end else begin pulse<=en && count==3; if(en) count<=count+1; end',
        'reg [1:0] count; always @(posedge clk) if(rst) begin count<=0; pulse<=0; end else if(en) begin pulse<=count==3; count<=count+1; end')
    def sequence(s,r,d):
        if r:return (0,0),0
        history,length=s
        new=((history<<1)|d)&7
        return (new,min(length+1,3)),int(length>=2 and new==5)
    stim=[(1,0)]+[(0,int(x)) for x in '101010110100101']+[(int(i%43==0),rng.randrange(2)) for i in range(256)]
    seq('sequence101','input wire clk, rst, din, output reg match',sync+'Registered serial 101 detector. Reset clears history and match. After each nonreset rising edge, match=1 iff the last three nonreset sampled bits are 1,0,1. Overlapping matches allowed (10101 gives two pulses). Fewer than three bits since reset cannot match.',
        [('rst',1),('din',1)],[('match',1)],stim,sequence,(0,0),
        'reg [1:0] hist; reg [1:0] count; always @(posedge clk) if(rst) begin hist<=0; count<=0; match<=0; end else begin match<=(count>=2 && hist==2 && din); hist<={hist[0],din}; if(count<2) count<=count+1; end',
        'reg [1:0] hist; always @(posedge clk) if(rst) begin hist<=0; match<=0; end else begin match<=(hist==1 && din); hist<={hist[0],din}; end')
    def fifo(s,r,w,rd,d):
        if r:s=[]
        else:
            old=list(s); s=list(s)
            if rd and old:s.pop(0)
            if w and len(old)<4:s.append(d)
        out=(int(len(s)==4)<<12)|(int(not s)<<11)|(len(s)<<8)|(s[0] if s else 0)
        return s,out
    stim=[(1,0,0,0)]+[(0,1,0,i+10) for i in range(6)]+[(0,1,1,99)]+[(0,0,1,0)]*6+[(0,1,1,33)]
    stim += [(int(i%79==0),rng.randrange(2),rng.randrange(2),rng.randrange(256)) for i in range(1024)]
    fifo_gold='''reg [7:0] mem [0:3]; reg [1:0] wp,rp;
wire push=wr_en && !full; wire pop=rd_en && !empty;
assign full=(count==4); assign empty=(count==0); assign rdata=empty ? 8'b0 : mem[rp];
always @(posedge clk) if(rst) begin wp<=0; rp<=0; count<=0; end else begin
 if(push) begin mem[wp]<=wdata; wp<=wp+1; end
 if(pop) rp<=rp+1;
 case({push,pop}) 2'b10:count<=count+1; 2'b01:count<=count-1; default:count<=count; endcase
end'''
    seq('fifo4x8','input wire clk, rst, wr_en, rd_en, input wire [7:0] wdata, output wire full, empty, output reg [2:0] count, output wire [7:0] rdata',
        sync+'FIFO depth 4, width 8. On reset empty=1, full=0, count=0. rdata is combinational oldest stored byte, or 0 when empty. At an edge accept write iff wr_en and pre-edge count<4; accept read iff rd_en and pre-edge count>0. Decisions use PRE-edge state independently: full+both requests only reads; empty+both requests only writes (no bypass). Accepted read removes oldest; accepted write appends wdata. Maintain count and order across pointer wrap.',
        [('rst',1),('wr_en',1),('rd_en',1),('wdata',8)],[('full',1),('empty',1),('count',3),('rdata',8)],stim,fifo,[],fifo_gold,fifo_gold.replace('wr_en && !full','wr_en && (!full || rd_en)'))
    (ROOT / 'tasks/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(manifest)} tasks; checks per complete suite: {sum(x["checks"] for x in manifest)}')


if __name__ == '__main__':
    build()
