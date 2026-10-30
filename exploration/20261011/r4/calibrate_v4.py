"""Small mechanism calibration, raw artifacts retained; not model research evidence."""
import sys,json,copy
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import tasks,intent,calibration_contracts as contracts,judge,batch,rtl_lab as lab,runner
RUN=BASE/'runs/calibration-v4';ASSETS=BASE/'assets-v1'
def main():
    assert not RUN.exists() and ASSETS.exists();RUN.mkdir(parents=True)
    for t,spec in tasks.TASKS.items():
        pub,priv=tasks.dataset(t);assert batch.read(ASSETS/(t+'.json'))==json.loads(json.dumps(spec));assert batch.read(ASSETS/(t+'-public.json'))==pub;assert batch.read(ASSETS/(t+'-private.json'))==priv
    for rel,h in batch.read(ASSETS/'lock.json').items():assert lab.digest((ASSETS/rel).read_bytes())==h
    batch.atomic(RUN/'source-lock.json',runner.hashes())
    evaluations=[];irchecks=[];manual=[]
    for task in tasks.TASKS:
        spec=tasks.TASKS[task];reference=(BASE/'references'/(task+'.sv')).read_text(encoding='utf-8');public=batch.read(ASSETS/(task+'-public.json'));private=batch.read(ASSETS/(task+'-private.json'))
        for scope,rows in [('public',public),('private',private)]:
            folder=RUN/task/'correct'/scope;result=judge.simulate(folder,task,reference,rows);batch.atomic(folder/'judge.json',result);assert result['status']=='PASS';evaluations.append(dict(task=task,fixture='correct',scope=scope,result=result))
            for rep in ('structured','linear'):
                raw=intent.serialize(contracts.contract(task),rep);irfolder=RUN/task/'intent-correct'/rep/scope;irfolder.mkdir(parents=True);(irfolder/'response.txt').write_bytes(raw.encode());result,values=intent.check(raw,rep,task,rows);batch.atomic(irfolder/'judge.json',result);assert result['status']=='PASS';irchecks.append(dict(task=task,representation=rep,scope=scope,result=result))
        bad=reference.replace('l0<=t0','l0<=s0').replace('l1<=t1','l1<=s1') if task=='epoch_commit' else reference.replace('credit<=funded-cost','credit<=credit-cost') if task=='refund_credit' else reference.replace('ta1==tb1','ta==tag_b')
        assert bad!=reference
        for scope,rows in [('public',public),('private',private)]:
            folder=RUN/task/'target-mutant'/scope;result=judge.simulate(folder,task,bad,rows);batch.atomic(folder/'judge.json',result);assert result['status']=='FUNCTION_FAIL';evaluations.append(dict(task=task,fixture='target-mutant',scope=scope,result=result))
        p=contracts.contract(task);p['timing']['reset']='sync_low';raw=intent.serialize(p,'structured');result,_=intent.check(raw,'structured',task,private);assert result['status']=='FUNCTION_FAIL';irchecks.append(dict(task=task,fixture='sync-reset-mutant',scope='private',result=result));batch.atomic(RUN/task/'sync-reset-intent.json',dict(raw=raw,result=result))
    task='refund_credit';ref=(BASE/'references'/(task+'.sv')).read_text();bad=ref.replace('end end\nendmodule','if(credit==5 && refund==3 && submit && cost==1) credit<=0;\nend end\nendmodule')
    for scope in ('public','private'):
        folder=RUN/task/'public-blindspot'/scope;result=judge.simulate(folder,task,bad,batch.read(ASSETS/(task+'-'+scope+'.json')));batch.atomic(folder/'judge.json',result);assert result['status']==('PASS' if scope=='public' else 'FUNCTION_FAIL');evaluations.append(dict(task=task,fixture='public-blindspot',scope=scope,result=result))
    folder=RUN/'syntax';result=judge.simulate(folder,task,ref.replace('credit<=0','credit<= ;'),batch.read(ASSETS/(task+'-public.json')));batch.atomic(folder/'judge.json',result);assert result['status']=='COMPILE_FAIL';evaluations.append(dict(task=task,fixture='syntax',scope='public',result=result))
    tests=[('epoch_commit',0,2),('epoch_commit',2,25),('epoch_commit',4,24),('refund_credit',0,24),('refund_credit',1,29),('refund_credit',2,4),('tagged_join',2,5),('tagged_join',3,7)]
    for t,edge,expected in tests:
        rows=batch.read(ASSETS/(t+'-public.json'));event=4+5*edge;assert rows[event]['expected']==expected;manual.append(dict(task=t,event=event,hand_expected=expected,observed=rows[event]['expected']))
    rows=batch.read(ASSETS/'tagged_join-public.json');base=3+5*len(tasks.sequences('tagged_join')[0]);assert rows[base+9]['expected']==24;manual.append(dict(task='tagged_join',event=base+9,hand_expected=24,observed=24))
    invalids=[]
    for label,raw,rep,expected in [('multi','```json\n{}\n```\n```json\n{}\n```','structured','EXTRACTION_ERROR'),('oversize','x'*16385,'linear','EXTRACTION_ERROR'),('empty','', 'linear','EXTRACTION_ERROR'),('syntax','not-json','structured','EXTRACTION_ERROR')]:
        result,_=intent.check(raw,rep,'epoch_commit',batch.read(ASSETS/'epoch_commit-public.json'));assert result['status']==expected;invalids.append(dict(label=label,raw=raw,result=result))
    for label,mutate,expected in [('width',lambda p:p['registers']['mask'].update(width=9),'UNSUPPORTED'),('call',lambda p:p['next'].update(mask='open(1)'),'UNSUPPORTED'),('missing',lambda p:p['next'].pop('mask'),'IR_INVALID')]:
        p=contracts.contract('epoch_commit');mutate(p);raw=intent.serialize(p,'structured');result,_=intent.check(raw,'structured','epoch_commit',batch.read(ASSETS/'epoch_commit-public.json'));assert result['status']==expected;invalids.append(dict(label=label,raw=raw,result=result))
    batch.atomic(RUN/'evaluations.json',evaluations);batch.atomic(RUN/'intent-checks.json',irchecks);batch.atomic(RUN/'manual-witnesses.json',manual);batch.atomic(RUN/'invalid-cases.json',invalids)
    summary=dict(status='PASS',real_model_calls=0,label='MECHANISM_CALIBRATION_ONLY',compile_evaluations=len(evaluations),simulator_receipts=sum((RUN/t).exists() for t in [])+len(list(RUN.rglob('simulate.json'))),intent_checks=len(irchecks),invalid_intent_cases=len(invalids),hand_witnesses=len(manual),target_mutants_private_detected=3,target_mutants_public_detected=3,public_blindspot=dict(public='PASS',private='FUNCTION_FAIL'),events={t:{s:len(batch.read(ASSETS/(t+'-'+s+'.json'))) for s in ('public','private')} for t in tasks.TASKS})
    batch.atomic(RUN/'summary.json',summary);runner.seal(RUN);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
