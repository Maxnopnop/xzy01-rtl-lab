"""Targeted reservation accounting correction; original full-flow evidence retained."""
import sys,json,difflib
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import runner_v2 as runner,batch,rtl_lab as lab
RUN=BASE/'runs/unknown-v2'
def main():
    assert not RUN.exists();RUN.mkdir(parents=True);p=runner.plan();j=p['jobs'][0];folder=RUN/'unknown/jobs'/j['id'];folder.mkdir(parents=True);batch.atomic(folder/'started.json',dict(reserved_calls=1));calls=[]
    def fail(*args):calls.append(1);raise AssertionError('No resend permitted')
    result=runner.campaign(RUN/'unknown',p,fail);assert result['status']=='STOPPED_INFRASTRUCTURE' and not calls
    assert runner.campaign(RUN/'unknown',p,fail)==result and not calls
    # score checks no hidden rows for unknown/pending; uses true fixed planned slots.
    summary=runner.score(RUN/'unknown',p);assert summary['started']==1 and summary['statuses']==dict(UNKNOWN_INTERRUPTED=1,PENDING=47)
    assert all(s['denominator']==6 and s['passes']==0 for s in summary['strategies'].values())
    # Only gate/path and reservation metadata differ from original full-flow-tested runner.
    old=(BASE/'runner.py').read_text(encoding='utf-8');new=(BASE/'runner_v2.py').read_text(encoding='utf-8')
    expected=old.replace("RUN=BASE/'runs/prepared-v1'","RUN=BASE/'runs/prepared-v2'").replace("assert not RUN.exists();RUN.mkdir","assert batch.read(BASE/'runs/unknown-v2/summary.json')['status']=='PASS'\n    assert not RUN.exists();RUN.mkdir").replace("result=dict(status='UNKNOWN_INTERRUPTED',usage=None)","result=dict(status='UNKNOWN_INTERRUPTED',usage=None,model_called=True,reservation_unknown=True)").replace("dict(status='UNKNOWN_INTERRUPTED',usage=None))","dict(status='UNKNOWN_INTERRUPTED',usage=None,model_called=True,reservation_unknown=True))")
    assert new==expected
    (RUN/'runner-diff.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='runner.py',tofile='runner_v2.py')),encoding='utf-8')
    batch.atomic(RUN/'summary.json',dict(status='PASS',real_model_calls=0,mock_adapter_calls=0,simulator_calls=0,reserved_unknown=1,pending=47,no_resend=True,label='ENGINEERING_ONLY; model_called is conservative reservation marker, not confirmed provider invocation'))
    batch.atomic(RUN/'source-lock.json',runner.hashes());runner.seal(RUN);print('Unknown reservation accounting PASS; 0 model/adapter/simulator calls')
if __name__=='__main__':main()
