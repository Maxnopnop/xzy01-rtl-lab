"""Event-level asynchronous reset and Moore hold checks, independent oracle."""
import sys,json,itertools,time,re
from pathlib import Path
from collections import Counter,defaultdict
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import batch,rtl_lab as lab,paired_bank as bank,mutation_study as ms,backends,r1b_v2
TASKS=r1b_v2.TASKS

def events(task):
    out=[];clk=0;rst=1;din=0;history=[];q=None
    def emit(c,r,b,kind):
        nonlocal clk,rst,din,history,q
        if r==0:history=[(0,b)];q=bank.oracle(task,history)[-1][3]
        elif c==1 and clk==0:
            history.append((1,b));q=bank.oracle(task,history)[-1][3]
        out.append(dict(clk=c,reset=r,bit=b,expected=q,category=kind));clk,rst,din=c,r,b
    def cycle(b):
        emit(0,1,b,'input_low');emit(0,1,1-b,'hold_low_flip');emit(0,1,b,'hold_low_restore')
        emit(1,1,b,'posedge');emit(1,1,1-b,'hold_high_flip');emit(1,1,b,'hold_high_restore');emit(0,1,b,'negedge_hold')
    for n in range(6):
        for prefix in itertools.product((0,1),repeat=n):
            for phase,mode,b in itertools.product((0,1),('pulse','cross_edge','coincident'),(0,1)):
                emit(0,0,0,'episode_reset');emit(0,1,0,'initial_release')
                for x in prefix:cycle(x)
                emit(phase,1,b,'prepare_reset_phase')
                emit(1 if mode=='coincident' else phase,0,b,'reset_assert_'+mode)
                emit(1 if mode=='coincident' else phase,0,1-b,'reset_input_flip')
                if mode=='cross_edge':emit(0,0,b,'reset_low');emit(1,0,b,'reset_posedge')
                emit(1 if mode in ('coincident','cross_edge') else phase,1,b,'reset_release_'+mode)
                emit(0,1,b,'post_reset_negedge')
                for x in '100110010110':cycle(int(x))
    return out

def simulate(folder,spec,dut,rows,tools,args):
    folder.mkdir(parents=True);(folder/'dut.sv').write_bytes(dut)
    lab.extract_rtl(dut.decode('utf-8'),spec['module'])
    r,b,q=(spec['ports'][k] for k in ('reset_port','input_port','output_port'))
    values=[f'{e["clk"]}{e["reset"]}{e["bit"]}{e["expected"]}' for e in rows];lab.write_text(folder/'events.bin','\n'.join(values)+'\n')
    tb=f'''module tb; reg clk=0;reg {r}=1;reg {b}=0;wire {q};reg [3:0] vectors[0:{len(rows)-1}];integer i,count=0,errors=0,fd;reg [255:0] nonce;
{spec['module']} D(.clk(clk),.{r}({r}),.{b}({b}),.{q}({q}));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish; $readmemb("events.bin",vectors);
for(i=0;i<{len(rows)};i=i+1) begin {{clk,{r},{b}}}=vectors[i][3:1]; #2;count=count+1;
if({q} !== vectors[i][0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d clk=%0d reset=%0d input=%0d expected=%0d observed=%0b",i,clk,{r},{b},vectors[i][0],{q});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,count,errors);$fclose(fd);$finish;end endmodule
'''
    lab.write_text(folder/'testbench.sv',tb);row=backends.IcarusBackend().evaluate(folder,dict(checks=len(rows)),tools,args)
    pattern=r'MISMATCH event=(\d+) clk=(\d) reset=(\d) input=(\d) expected=(\d) observed=([01xz])'
    row['mismatches']=[dict(event=int(i),clk=int(c),reset=int(rst),input=int(bit),expected=int(e),observed=o,category=rows[int(i)]['category']) for i,c,rst,bit,e,o in re.findall(pattern,(folder/'simulate.stdout.log').read_text(encoding='utf-8') if (folder/'simulate.stdout.log').exists() else '')]
    row.update(dut_sha256=lab.digest(dut),tb_sha256=lab.digest((folder/'testbench.sv').read_bytes()),events_sha256=lab.digest((folder/'events.bin').read_bytes()));return row

def selection():
    groups=defaultdict(list);aliases=defaultdict(list)
    for exp in ('fsm48','paired-a32','paired-b64'):
        for p in sorted((ROOT/'evidence'/exp/'jobs').glob('*/result.json')):
            r=batch.read(p)
            if r.get('task') not in TASKS or r['status']!='PASS':continue
            dut=p.parent/'dut.sv';sha=lab.digest(dut.read_bytes());assert sha==r['rtl_sha256']
            item=dict(result_path=str(p.relative_to(ROOT)),dut_path=str(dut.relative_to(ROOT)),result_sha256=lab.digest(p.read_bytes()),rtl_sha256=sha,task=r['task'],model=r['requested_model'],original_status=r['status'])
            groups[item['task'],item['model']].append(item);aliases[sha].append(item)
    chosen=[];seen=set()
    while any(groups.values()) and len(chosen)<64:
        for key in sorted(groups):
            while groups[key] and groups[key][0]['rtl_sha256'] in seen:groups[key].pop(0)
            if groups[key] and len(chosen)<64:
                item=groups[key].pop(0);seen.add(item['rtl_sha256']);chosen.append(item)
    return dict(rows=chosen,aliases={h:xs for h,xs in aliases.items() if len(xs)>1},total_original_pass_records=sum(len(v) for v in aliases.values()),distinct_hashes=len(aliases),cap=64)

def main():
    run=HERE/'runs/timed-reset-v1'
    if run.exists():raise ValueError('Immutable run exists')
    run.mkdir(parents=True);start=time.monotonic();specs={s['id']:s for s in ms.development_specs()};selected=selection();profiles={t:events(t) for t in TASKS}
    batch.atomic(run/'selection.json',selected);batch.atomic(run/'events.json',profiles)
    paths=[Path(__file__),HERE/'R1C_PROTOCOL.md',HERE/'r1b_v2.py',ROOT/'paired_bank.py',ROOT/'rtl_lab.py',ROOT/'backends.py',ROOT/'mutation_study.py',ROOT/'fsm_ir.py',ROOT/'batch.py',bank.ROOT/'bank-lock.json']
    batch.atomic(run/'plan.json',dict(kind='R1C_EVENT_RESET_AND_HOLD',new_model_calls=0,created_utc=lab.utc(),source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths},selection_sha256=lab.digest((run/'selection.json').read_bytes()),event_sha256=lab.digest((run/'events.json').read_bytes()),event_counts={t:len(x) for t,x in profiles.items()}))
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10);tools=lab.inspect_tools(args,run);batch.atomic(run/'environment.json',tools);cal=[]
    def check(label,task,text,expected):
        row=simulate(run/'calibration'/label,specs[task],text.encode(),profiles[task],tools,args);cal.append(dict(label=label,task=task,expected=expected,**row));batch.atomic(run/'calibration.json',cal);print('CAL',label,row['status'],flush=True);assert row['status']==expected,(label,row)
    for t in TASKS:check('correct_'+t,t,r1b_v2.reference(t,specs[t]['module'],specs[t]['ports']),'PASS')
    t='event_parity';base=r1b_v2.reference(t,specs[t]['module'],specs[t]['ports'])
    for label,text in [('sync_reset',base.replace(' or negedge rst_n','')),('reset_priority',base.replace('if(!rst_n)','if(!rst_n && !din)')),('input_leak',base.replace('q=parity','q=parity^din')),('wrong_edge',base.replace('posedge clk','negedge clk'))]:check(label,t,text,'FUNCTION_FAIL')
    check('syntax_error',t,base.replace('parity<=','parity<= ; broken ',1),'COMPILE_FAIL')
    results=[];infra=0
    for i,item in enumerate(selected['rows']):
        if time.monotonic()-start>600:break
        dut=(ROOT/item['dut_path']).read_bytes();assert lab.digest(dut)==item['rtl_sha256'];assert lab.digest((ROOT/item['result_path']).read_bytes())==item['result_sha256']
        folder=run/'history'/f'{i:02d}_{item["task"]}'
        try:row=simulate(folder,specs[item['task']],dut,profiles[item['task']],tools,args)
        except lab.LabError as exc:row=dict(status='UNSUPPORTED',message=exc.message)
        if row['status']=='FUNCTION_FAIL':
            first=row['mismatches'][0]['event'];row['short_witness']=simulate(folder/'witness',specs[item['task']],dut,profiles[item['task']][:first+1],tools,args);assert row['short_witness']['status']=='FUNCTION_FAIL'
        results.append(dict(selection_index=i,source=item,result=row));batch.atomic(run/'history-results.json',results);print('HISTORY',i,item['task'],row['status'],flush=True)
        infra=infra+1 if row['status'] in ('ENV_ERROR','TIMEOUT','SIM_ERROR') else 0
        if infra>=3:break
    summary=dict(kind='R1C_EVENT_RESET_AND_HOLD',planned=len(selected['rows']),completed=len(results),pending=len(selected['rows'])-len(results),statuses=dict(Counter(r['result']['status'] for r in results)),new_error_indices=[r['selection_index'] for r in results if r['result']['status']=='FUNCTION_FAIL'],icarus_evaluations=len(cal)+len(results)+sum('short_witness' in r['result'] for r in results),elapsed_seconds=time.monotonic()-start,model_calls=0,cost=0,limits='Discrete event-set simulation, five development families, not analog reset or exhaustive temporal proof. Original scores unchanged.')
    batch.atomic(run/'summary.json',summary);batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()})
if __name__=='__main__':main()
