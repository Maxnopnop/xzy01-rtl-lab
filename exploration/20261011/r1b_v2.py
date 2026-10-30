"""Bounded SAT calibration and frozen selection of real retained model RTL."""
import sys,json,re,time,copy,itertools
from pathlib import Path
from collections import Counter,defaultdict
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import batch,rtl_lab as lab,paired_bank as bank,mutation_study as ms,fsm_ir,fsm_checks
TASKS=['rt_sequence','sticky_alarm','event_parity','request_delay','debounce3']

BODY={
'rt_sequence':"reg [3:0] history; always @(posedge clk or negedge rst_n) if(!rst_n) history<=0; else history<={history[2:0],din}; assign q=history==4'b1001;",
'sticky_alarm':"reg previous,alarm; always @(posedge clk or negedge rst_n) if(!rst_n) begin previous<=0;alarm<=0;end else begin previous<=din;alarm<=alarm|(previous&din);end assign q=alarm;",
'event_parity':"reg parity; always @(posedge clk or negedge rst_n) if(!rst_n) parity<=0; else parity<=parity^din; assign q=parity;",
'request_delay':"reg [1:0] phase; always @(posedge clk or negedge rst_n) if(!rst_n) phase<=0; else if(phase==0) begin if(din) phase<=1;end else if(phase==1) phase<=2; else if(phase==2) phase<=3; else if(!din) phase<=0; assign q=phase==2;",
'debounce3':"reg high;reg [1:0] streak; always @(posedge clk or negedge rst_n) if(!rst_n) begin high<=0;streak<=0;end else if(din==high) streak<=0;else if((!high && streak==2)||(high && streak==1)) begin high<=!high;streak<=0;end else streak<=streak+1; assign q=high;"}

def reference(task,module='gold',ports=None):
    text='module '+module+'(input clk,input rst_n,input din,output q);\n'+BODY[task]+'\nendmodule\n'
    if ports:
        for a,b in [('rst_n',ports['reset_port']),('din',ports['input_port']),('q',ports['output_port'])]:text=re.sub(r'\b'+a+r'\b',b,text)
    return text

def classify(result):
    text=result['stdout']+'\n'+result['stderr']
    if result.get('timeout'):return 'TIMEOUT'
    if result.get('output_limit'):return 'OUTPUT_LIMIT'
    if result['returncode']!=0:
        if 'syntax error' in text.lower():return 'SYNTAX_ERROR'
        if any(x in text for x in ('Failed to import cell','Unsupported cell type','Multiple edge sensitive','multiple edge sensitive')):return 'UNSUPPORTED'
        return 'TOOL_ERROR'
    if 'SAT proof finished - model found: FAIL!' in text:return 'COUNTEREXAMPLE_FOUND'
    if 'SAT proof finished - no model found: SUCCESS!' in text:return 'NO_COUNTEREXAMPLE_WITHIN_BOUND'
    return 'UNPARSED_TOOL_RESULT'

def sat(folder,task,dut,spec,bound,timeout=30):
    folder.mkdir(parents=True)
    original=dut;lab.extract_rtl(original,spec['module'])
    dut,n=re.subn(r'\bmodule\s+'+re.escape(spec['module'])+r'\b','module gate',original,count=1)
    if n!=1:raise ValueError('Cannot map module')
    r,b,q=(spec['ports'][k] for k in ('reset_port','input_port','output_port'))
    top=f'\nmodule miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.{r}(rst_n),.{b}(din),.{q}(a));assign mismatch=g^a;endmodule\n'
    (folder/'original.sv').write_bytes(original.encode('utf-8'));(folder/'mapped.sv').write_bytes(dut.encode('utf-8'));lab.write_text(folder/'reference.sv',reference(task));lab.write_text(folder/'miter.sv',reference(task)+dut+top)
    constraints=' '.join(f'-set-at {i} rst_n {int(i>1)}' for i in range(1,bound+1))
    script='read_verilog -sv miter.sv\nhierarchy -top miter\nproc\nflatten\nopt\nasync2sync\nopt\nsat -seq '+str(bound)+' -set-init-zero '+constraints+' -prove mismatch 0 -show din -show rst_n -show mismatch -dump_json trace.json\n'
    lab.write_text(folder/'check.ys',script);absolute=folder.resolve().as_posix();linux='/mnt/'+absolute[0].lower()+absolute[2:]
    try:res=lab.run_process(['wsl','-d','Ubuntu','--cd',linux,'--','yosys','-s','check.ys'],folder,timeout);lab.save_process(folder,'yosys',res);status=classify(res)
    except OSError as exc:return dict(status='ENV_ERROR',message=str(exc),bound=bound)
    return dict(status=status,bound=bound,elapsed_seconds=res['elapsed_seconds'],returncode=res['returncode'],original_sha256=lab.digest(original.encode()),mapped_sha256=lab.digest(dut.encode()),miter_sha256=lab.digest((folder/'miter.sv').read_bytes()),directory=str(folder.relative_to(HERE)))

def select():
    candidates=[];excluded=Counter()
    for experiment in ('fsm48','paired-a32','paired-b64'):
        for p in sorted((ROOT/'evidence'/experiment/'jobs').glob('*/result.json')):
            row=batch.read(p)
            if row.get('task') not in TASKS:excluded['task_without_independent_reference']+=1;continue
            if row['status'] not in ('PASS','FUNCTION_FAIL'):excluded[row['status']]+=1;continue
            dut=p.parent/'dut.sv';h=lab.digest(dut.read_bytes());assert h==row['rtl_sha256']
            candidates.append(dict(experiment=experiment,result_path=str(p.relative_to(ROOT)),dut_path=str(dut.relative_to(ROOT)),result_sha256=lab.digest(p.read_bytes()),rtl_sha256=h,task=row['task'],model=row['requested_model'],original_status=row['status'],original_localization=row.get('localization')))
    candidates.sort(key=lambda r:r['result_path']);selected=[r for r in candidates if r['original_status']=='FUNCTION_FAIL']
    assert len(selected)<=24
    passed=defaultdict(list)
    for r in candidates:
        if r['original_status']=='PASS':passed[r['task'],r['model']].append(r)
    for key in sorted(passed):selected.append(passed[key].pop(0))
    while len(selected)<24 and any(passed.values()):
        for key in sorted(passed):
            if len(selected)>=24:break
            if passed[key]:
                hashes={r['rtl_sha256'] for r in selected};idx=next((i for i,r in enumerate(passed[key]) if r['rtl_sha256'] not in hashes),0)
                selected.append(passed[key].pop(idx))
    return selected,dict(excluded)

def witness(folder,task,dut,spec,trace,tools,args):
    def decode(wave):
        out=[];last=None
        for c in wave:
            if c in '01':last=int(c)
            elif c!='.':last=None
            out.append(last)
        return out
    waves={s['name']:decode(s['wave']) for s in trace['signal']}
    rst=waves['rst_n'];bits=waves['din'];mismatch=waves['mismatch'];at=next(i for i,x in enumerate(mismatch) if x==1)
    if at<2 or any(b not in (0,1) for b in bits[2:at]):return dict(status='COUNTEREXAMPLE_NOT_REPRODUCED',reason='Initial/reset-only or X trace')
    inputs=[(0,0)]+[(1,b) for b in bits[2:at]]
    # Expected vectors use independent Python procedural oracle, not IR/compiler.
    rows=bank.oracle(task,inputs)
    # Existing write_agreement_test uses IR, so emit an independent fixed TB here.
    r,b,q=(spec['ports'][k] for k in ('reset_port','input_port','output_port'))
    folder.mkdir(parents=True);(folder/'dut.sv').write_bytes(dut.encode('utf-8'))
    lines=['module tb;reg clk=0;reg '+r+'=1;reg '+b+'=0;wire '+q+';integer errors=0;integer count=0;integer receipt;reg [8*128-1:0] nonce;',spec['module']+f' D(.clk(clk),.{r}({r}),.{b}({b}),.{q}({q}));','initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;']
    for reset,bit,pre,post in rows:
        lines+=[f'clk=0; {r}={reset}; {b}={bit}; #2; count=count+1; if({q} !== 1\'b{pre}) errors=errors+1;',f'clk=1; #2; count=count+1; if({q} !== 1\'b{post}) errors=errors+1;']
    lines+=['receipt=$fopen("verdict.txt","w"); $fdisplay(receipt,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,count,errors);$fclose(receipt);$finish;end endmodule']
    lab.write_text(folder/'testbench.sv','\n'.join(lines));import backends
    result=backends.IcarusBackend().evaluate(folder,dict(module=spec['module'],checks=2*len(rows)),tools,args)
    return dict(result,inputs=inputs,solver_mismatch_step=at,expected_post=[r[3] for r in rows],tb_sha256=lab.digest((folder/'testbench.sv').read_bytes()))

def lock(run):batch.atomic(run/'evidence-lock.json',{str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})

def main():
    run=HERE/'runs/r1b-v2'
    if run.exists():raise ValueError('Immutable run exists')
    run.mkdir(parents=True);start=time.monotonic();specs={s['id']:s for s in ms.development_specs()};selection,excluded=select()
    batch.atomic(run/'selection.json',dict(rows=selection,excluded=excluded,rule='Original failures, task/model PASS strata, round robin; frozen before SAT'))
    paths=[Path(__file__),HERE/'R1B_PROTOCOL.md',HERE/'R1B_AMENDMENT.md',ROOT/'rtl_lab.py',ROOT/'backends.py',ROOT/'fsm_checks.py',ROOT/'fsm_ir.py',ROOT/'paired_bank.py',ROOT/'mutation_study.py',ROOT/'batch.py',bank.ROOT/'bank-lock.json',HERE/'runs/delayed-v1/cases.json']
    batch.atomic(run/'plan.json',dict(kind='R1B_SAT_CALIBRATION_AND_REAL_MODEL_REPLAY',created_utc=lab.utc(),new_model_calls=0,selection_sha256=lab.digest((run/'selection.json').read_bytes()),source_hashes={str(p.relative_to(ROOT)):lab.digest(p.read_bytes()) for p in paths},max_yosys=57,history_bounds=[14,32],timeout=30,scope='tick-level forced initial reset, zero init, async2sync; bounded only'))
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10);tools=lab.inspect_tools(args,run);batch.atomic(run/'environment.json',tools)
    env=lab.run_process(['wsl','-d','Ubuntu','--','yosys','-V'],run,15);lab.save_process(run,'version',env)
    references=[]
    for task in TASKS:
        spec=specs[task];row=ms.fixed_sim(run/'references'/task,spec,reference(task,spec['module'],spec['ports']),tools,args);references.append(dict(task=task,**row));assert row['status']=='PASS',row
    batch.atomic(run/'references.json',references)
    calibrations=[]
    def check(label,task,dut,bound,expected):
        row=sat(run/'calibration'/label,task,dut,specs[task],bound);row.update(label=label,expected=expected);calibrations.append(row);batch.atomic(run/'calibration.json',calibrations);print('CAL',label,row['status'],flush=True);assert row['status']==expected,row
    for task in TASKS:check('correct_'+task,task,bank.fixture_rtl(bank.graph(task),specs[task]['ports'],specs[task]['module']),14,'NO_COUNTEREXAMPLE_WITHIN_BOUND')
    task='rt_sequence';obj=copy.deepcopy(bank.graph(task)['data']);names={s['name']:'REN'+str(i) for i,s in enumerate(obj['states'])}
    for s in obj['states']:s['name']=names[s['name']]
    for e in obj['transitions']:e['from']=names[e['from']];e['to']=names[e['to']]
    obj['reset']['state']=names[obj['reset']['state']]
    check('equivalent_renamed',task,bank.fixture_rtl(fsm_ir.parse(json.dumps(obj)),specs[task]['ports'],specs[task]['module']),14,'NO_COUNTEREXAMPLE_WITHIN_BOUND')
    case=next(c for c in batch.read(HERE/'runs/delayed-v1/cases.json') if c['task']==task);bad=bank.fixture_rtl(fsm_ir.parse(json.dumps(case['ir'])),specs[task]['ports'],specs[task]['module'])
    check('delayed_short',task,bad,12,'NO_COUNTEREXAMPLE_WITHIN_BOUND');check('delayed_sufficient',task,bad,14,'COUNTEREXAMPLE_FOUND')
    check('real_syntax_error',task,bad.replace('state <=','state <= ; broken ',1),14,'SYNTAX_ERROR')
    rows=[];errors=0
    for i,item in enumerate(selection):
        if time.monotonic()-start>900:break
        p=ROOT/item['dut_path'];assert lab.digest(p.read_bytes())==item['rtl_sha256'];assert lab.digest((ROOT/item['result_path']).read_bytes())==item['result_sha256']
        dut=p.read_bytes().decode('utf-8');task=item['task'];spec=specs[task];results=[]
        for bound in (14,32):
            folder=run/'history'/f'{i:02d}_{task}'/str(bound)
            try:row=sat(folder,task,dut,spec,bound)
            except lab.LabError as exc:row=dict(status='UNSUPPORTED',message=exc.message,bound=bound)
            if row['status']=='COUNTEREXAMPLE_FOUND':row['witness']=witness(folder/'witness',task,dut,spec,batch.read(folder/'trace.json'),tools,args)
            results.append(row)
        row=dict(selection_index=i,source=item,results=results);rows.append(row);batch.atomic(run/'history-results.json',rows);print('HISTORY',i,task,item['original_status'],[r['status'] for r in results],flush=True)
        errors=errors+1 if all(r['status'] in ('ENV_ERROR','TIMEOUT') for r in results) else 0
        if errors>=3:break
    statuses=Counter(r['status'] for x in rows for r in x['results']);new=[x['selection_index'] for x in rows if x['source']['original_status']=='PASS' and any(r.get('witness',{}).get('status')=='FUNCTION_FAIL' for r in x['results'])]
    batch.atomic(run/'summary.json',dict(kind='R1B_SAT_CALIBRATION_AND_REAL_MODEL_REPLAY',calibration_passed=True,calibration_cases=len(calibrations),selected=len(selection),completed=len(rows),pending=len(selection)-len(rows),history_sat_statuses=dict(statuses),new_counterexamples_on_original_pass=new,known_failure_reproduced_indices=[x['selection_index'] for x in rows if x['source']['original_status']=='FUNCTION_FAIL' and any(r.get('witness',{}).get('status')=='FUNCTION_FAIL' for r in x['results'])],icarus_evaluations=5+sum('witness' in r for x in rows for r in x['results']),yosys_commands=len(calibrations)+sum(len(x['results']) for x in rows),elapsed_seconds=time.monotonic()-start,model_calls=0,token_usage=None,cost=0,limits='Selection biased to historical failure strata, five development families. No counterexample is bounded evidence only; no method gain or natural error prevalence. Original scores unchanged.'))
    lock(run)
if __name__=='__main__':main()
