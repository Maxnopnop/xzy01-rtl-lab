"""Small frozen development calibration, not natural model evidence."""
import json,sys
from pathlib import Path
import tasks,reference_alt,intent,teacher,judge,stream_process as s
BASE=Path(__file__).resolve().parent;RUN=BASE/'runs/calibration-v1';ASSET=BASE/'assets'
assert not RUN.exists();RUN.mkdir(parents=True);ASSET.mkdir(exist_ok=True)
anchors={'ordered_retire':[8,16,16,16,13,6,2], 'restoring_divide':[512,512,512,512,512,321,65], 'tagged_join':[256,384,91,475,219,475,475,102]}
mutate={'ordered_retire':('pop=(count!=0 && d0)','pop=(count!=0 && (d0 || (finish && finish_tag==t0)))'),
        'restoring_divide':('if(left==1)','if(left==2)'),
        'tagged_join':('at<bt','at>bt')}
receipts=[]
try:
    for task in tasks.TASKS:
        public,private=tasks.datasets(task)
        for name,rows in [('public',public),('private',private)]:
            assert reference_alt.run(task,rows)==[r['expected'] for r in rows],task+' alt '+name
            status,values=intent.check(teacher.make(task),'structured',task,rows)
            assert status['status']=='PASS',(task,status)
            s.atomic(ASSET/(task+'-'+name+'.json'),rows)
        assert [r['expected'] for r in public if r['category']=='rising']==anchors[task]
        s.atomic(RUN/(task+'-hand-anchors.json'),dict(status='PASS',derivation='Hand calculations written before simulation; see REFERENCE_AUDIT',expected=anchors[task]))
        raw=(BASE/'references'/(task+'.sv')).read_text()
        for name,rows in [('public',public),('private',private)]:
            r=judge.simulate(RUN/task/name,task,raw,rows);s.atomic(RUN/task/(name+'-judge.json'),r);receipts.append(r)
            assert r['status']=='PASS',(task,name,r)
        a,b=mutate[task];assert a in raw
        r=judge.simulate(RUN/task/'target-negative',task,raw.replace(a,b),private);s.atomic(RUN/task/'negative-judge.json',r);receipts.append(r)
        assert r['status']=='FUNCTION_FAIL',(task,'negative',r)
    s.atomic(ASSET/'lock.json',{p.name:s.digest(p.read_bytes()) for p in ASSET.glob('*.json') if p.name!='lock.json'})
    s.atomic(RUN/'summary.json',dict(status='PASS',label='ARTIFICIAL_DEVELOPMENT_CALIBRATION',model_calls=0,simulations=len(receipts),anchors=anchors,
                                  references='Same author, independent derivation paths; no external independent author',receipts=receipts))
except BaseException as e:
    s.atomic(RUN/'failure.json',dict(type=type(e).__name__,message=str(e),receipts=receipts));raise
finally:
    s.atomic(RUN/'evidence-lock.json',{str(p.relative_to(RUN)):s.digest(p.read_bytes()) for p in RUN.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})
print('Calibration PASS; 9 simulations; 3 target faults; 0 models')
