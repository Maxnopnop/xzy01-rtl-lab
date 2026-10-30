"""Real compiler/simulator calibration of independent hand-written references."""
import sys,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import tasks,judge,runner,batch,rtl_lab as lab

def fixtures():
    refs={t:tasks.reference(t) for t in tasks.TASKS}
    out=[dict(label='correct_'+t,task=t,raw=r,hidden='PASS') for t,r in refs.items()]
    out.append(dict(label='equivalent_onehot',task='rotating_owner',raw=(BASE/'references/rotating_owner_onehot.sv').read_text(),hidden='PASS'))
    changes={
      'cancel_deadline':[('finish_over_cancel','else if(cancel)','else if(cancel && !finish)'),('early_timeout','remaining<=3','remaining<=2')],
      'retrigger_window':[('tick_beats_retrigger','if(trigger)','if(trigger && !(active && enable && tick))'),('ignores_pause','active && enable && tick','active && tick')],
      'elastic_slot':[('overwrites_stalled','in_valid && in_ready','in_valid'),('drops_replacement','in_valid && in_ready','in_valid && in_ready && !occupied')],
      'rotating_owner':[('loses_ownership_hold','owner==0 || retire','owner==0 || req0 || req1 || retire'),('fixed_priority','(owner!=0?new_pref:preference)?2\'d2:2\'d1','2\'d1')]
    }
    for t,edits in changes.items():
        for name,old,new in edits:
            assert old in refs[t],(t,old)
            out.append(dict(label=t+'__'+name,task=t,raw=refs[t].replace(old,new),hidden='FUNCTION_FAIL'))
    out.append(dict(label='real_syntax_error',task='cancel_deadline',raw=refs['cancel_deadline'].replace('remaining<=3','remaining<= ;'),hidden='COMPILE_FAIL'))
    return out

def main():
    run=BASE/'runs/calibration-v1';assert not run.exists();run.mkdir(parents=True)
    if not runner.ASSETS.exists():runner.freeze_assets()
    fixtures_data=fixtures();batch.atomic(run/'fixtures.json',fixtures_data);results=[]
    batch.atomic(run/'source-lock.json',runner.hashes())
    for f in fixtures_data:
        row=dict(label=f['label'],task=f['task'],expected_hidden=f['hidden'])
        for split in ('public','private'):
            result=judge.simulate(run/f['label']/split,f['task'],f['raw'],batch.read(runner.ASSETS/(f['task']+'-'+split+'.json')));row[split]=result
            print(f['label'],split,result['status'],flush=True)
        results.append(row);batch.atomic(run/'results.json',results)
    ok=all(r['private']['status']==r['expected_hidden'] for r in results) and all(r['public']['status']=='PASS' for r in results if r['expected_hidden']=='PASS')
    summary=dict(status='PASS' if ok else 'FAILED',model_calls=0,icarus_evaluations=len(results)*2,public_target_detected=sum(r['public']['status']=='FUNCTION_FAIL' for r in results if r['expected_hidden']=='FUNCTION_FAIL'),target_mutations=8,results=results,
                 limits='Bounded binary event tests; no analog/CDC/unbounded fairness proof. Equivalent reencoding calibrated for arbiter only.')
    batch.atomic(run/'summary.json',summary);runner.seal(run);assert ok,'Preserve this failed run; new version required'
if __name__=='__main__':main()
