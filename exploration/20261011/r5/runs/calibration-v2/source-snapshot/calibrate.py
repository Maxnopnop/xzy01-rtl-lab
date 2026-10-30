import json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import tasks,intent,teacher,reference_alt,runner,judge
lab=runner.lab;batch=runner.batch
RUN=BASE/'runs/calibration-v1'
def mutants(task,sv):
    if task=='phase_snapshot':return sv.replace('if(clear_sample) sampled<=0; else if(capture) sampled<=data;','if(capture) sampled<=data; else if(clear_sample) sampled<=0;')
    if task=='escape_frame':return sv.replace('else if(escaped)begin','else if(escaped && symbol!=1)begin')
    return sv.replace('hint<=(chosen+1)%4;','hint<=(hint+1)%4;')
def anchors():
    records=[]
    def trace(task,commands,expected):
        s=tasks.initial(task)
        for i,((edge,x),want) in enumerate(zip(commands,expected)):
            s=tasks.step(task,s,tasks.unpack(task,tasks.pack_input(task,**x)),edge)
            assert s==want,(task,i,s,want)
        records.append(dict(task=task,commands=commands,expected_states=expected,label='Hand calculated observable states; same author'))
    trace('phase_snapshot',[(1,dict(publish=1,data=2)),(0,dict(capture=1,data=3)),(1,dict(publish=1,data=1)),(0,dict(capture=1,clear_sample=1,data=2))],[dict(sampled=0,visible=0,published=1),dict(sampled=3,visible=0,published=1),dict(sampled=3,visible=3,published=1),dict(sampled=0,visible=3,published=1)])
    commands=[(1,dict(feed=f,symbol=z)) for f,z in [(1,0),(1,2),(0,1),(1,1),(1,3),(1,1)]]
    expected=[dict(active=1,escaped=0,work_sum=0,work_count=0,last_sum=0,last_count=0,completed=0),dict(active=1,escaped=1,work_sum=0,work_count=0,last_sum=0,last_count=0,completed=0),dict(active=1,escaped=1,work_sum=0,work_count=0,last_sum=0,last_count=0,completed=0),dict(active=1,escaped=0,work_sum=1,work_count=1,last_sum=0,last_count=0,completed=0),dict(active=1,escaped=0,work_sum=2,work_count=2,last_sum=0,last_count=0,completed=0),dict(active=0,escaped=0,work_sum=0,work_count=0,last_sum=2,last_count=2,completed=1)]
    trace('escape_frame',commands,expected)
    commands=[(1,dict(allocate=1))]*5+[(1,dict(release=1,release_id=2,allocate=1)),(1,dict(release=1,release_id=0)),(1,dict(allocate=1))]
    expected=[dict(occupied=m,hint=h,last_alloc=a,alloc_valid=v,rejected=b) for m,h,a,v,b in [(1,1,0,1,0),(3,2,1,1,0),(7,3,2,1,0),(15,0,3,1,0),(15,0,3,0,1),(15,3,2,1,0),(14,3,2,0,0),(15,1,0,1,0)]]
    trace('masked_ring_alloc',commands,expected);return records
def main():
    assert not RUN.exists();RUN.mkdir(parents=True);batch.atomic(RUN/'source-lock.json',runner.hashes());batch.atomic(RUN/'anchors.json',anchors())
    results=[];cross=[]
    for task in tasks.TASKS:
        public=batch.read(runner.ASSETS/f'{task}-public.json');private=batch.read(runner.ASSETS/f'{task}-private.json');p=teacher.contract(task)
        (RUN/(task+'-teacher.json')).write_text(json.dumps(p));sv=(BASE/'references'/f'{task}.sv').read_text();converted=teacher.convert(task,p);(RUN/(task+'-converted.sv')).write_text(converted)
        for label,rows in [('public',public),('private',private)]:
            assert reference_alt.answers(task,rows)==[r['expected'] for r in rows]
            ir,values=intent.check(json.dumps(p),'structured',task,rows);assert ir['status']=='PASS',(task,ir)
            cross.append(dict(task=task,split=label,events=len(rows),alternate='PASS',artificial_IR=ir))
            for name,text,want in [('reference',sv,'PASS'),('priority-mutant',mutants(task,sv),'FUNCTION_FAIL')]:
                r=judge.simulate(RUN/task/label/name,task,text,rows);results.append(dict(task=task,split=label,kind=name,expected=want,result=r));assert r['status']==want,(task,label,name,r)
        r=judge.simulate(RUN/task/'converter',task,converted,private);results.append(dict(task=task,split='private',kind='artificial-deterministic-converter',expected='PASS',result=r));assert r['status']=='PASS',(task,r)
    # Real compile failure; no repaired candidate and no simulator expected.
    task='phase_snapshot';r=judge.simulate(RUN/'syntax',task,'module phase_snapshot(input clk); broken syntax; endmodule',public)
    assert r['status']=='COMPILE_FAIL',r;results.append(dict(kind='syntax',expected='COMPILE_FAIL',result=r))
    invalid=[]
    for raw,want in [('{','EXTRACTION_ERROR'),('x'*16385,'EXTRACTION_ERROR'),('```json\n{}\n```','EXTRACTION_ERROR'),(json.dumps(dict(teacher.contract(task),next_falling={})), 'IR_INVALID')]:
        r,_=intent.check(raw,'structured',task,private);assert r['status']==want;invalid.append(r)
    p=teacher.contract(task);p['next_falling']['r_sampled']='data << capture';r,_=intent.check(json.dumps(p),'structured',task,private);assert r['status']=='UNSUPPORTED';invalid.append(r)
    batch.atomic(RUN/'crosscheck.json',cross);batch.atomic(RUN/'results.json',results)
    batch.atomic(RUN/'summary.json',dict(status='PASS',label='ARTIFICIAL CALIBRATION ONLY',real_model_calls=0,anchors=18,reference_methods='Incremental Python, hand SV, payload/set derivation; all same author',checks=results,invalid=invalid))
    runner.seal(RUN);print('CALIBRATION_PASS; 0 models')
if __name__=='__main__':main()
