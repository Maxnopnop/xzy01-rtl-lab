"""Synthetic post-freeze job-binding acceptance; saved output only."""
import importlib.util,shutil,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(BASE))
import stream_process as s
spec=importlib.util.spec_from_file_location('r6_recover_v2',Path(__file__).with_name('recover_batch.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
RUN=BASE/'runs/recovery-job-binding-v2';assert not RUN.exists();RUN.mkdir(parents=True)
receipts=[]
try:
    for mode in ['correct','swapped-prompt','wrong-model','wrong-parent']:
        run=RUN/mode;call=run/'jobs/known/call';call.parent.mkdir(parents=True)
        shutil.copytree(BASE/'runs/process-v3/writer-kill-clean',call)
        prompt=(call/'prompt.bin').read_bytes().decode();(call/'exact-prompt.txt').write_bytes(prompt.encode());s.atomic(call.parent/'started.json',dict(reserved_calls=1))
        j=dict(id='known',role='direct_first',prompt=prompt if mode!='swapped-prompt' else prompt+'different')
        if mode=='wrong-parent':j=dict(id='known',role='direct_second',task='ordered_retire',first_id='missing-parent')
        plan=dict(label='ARTIFICIAL_RECOVERY_FIXTURE',model='ARTIFICIAL_NO_MODEL' if mode!='wrong-model' else 'DIFFERENT_MODEL',jobs=[j]+[dict(id='pending'+str(i)) for i in range(47)])
        s.atomic(run/'plan.json',plan);s.atomic(run/'plan-lock.json',dict(sha256=s.digest((run/'plan.json').read_bytes())));(run/'run.lock').write_bytes(b'0')
        before={str(p.relative_to(run)):s.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()}
        rows=mod.recover(run,RUN/(mode+'-new-output'),artificial=True)
        assert rows[0]['status']==('GENERATED' if mode=='correct' else 'UNKNOWN_INTERRUPTED')
        if mode!='correct':assert rows[0]['usage'] is None
        assert len(rows)==48 and sum(r['status']=='PENDING' for r in rows)==47
        assert before=={str(p.relative_to(run)):s.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()}
        receipts.append(dict(case=mode,status='PASS',result=rows[0]['status'],pending=47,denominator=48))
    s.atomic(RUN/'summary.json',dict(status='PASS',label='ARTIFICIAL_OFFLINE_JOB_BINDING',model_calls=0,receipts=receipts))
except BaseException as e:s.atomic(RUN/'failure.json',dict(type=type(e).__name__,message=str(e)));raise
finally:s.atomic(RUN/'evidence-lock.json',{str(p.relative_to(RUN)):s.digest(p.read_bytes()) for p in RUN.rglob('*') if p.is_file() and p!=RUN/'evidence-lock.json'})
print('Job/parent/prompt recovery binding PASS; 4 cases; 0 model calls')
