"""Offline control and information-boundary tests; adapter is always mocked."""
import sys,copy,json
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import runner,tasks,judge,batch,rtl_lab as lab

def plan_fixture():
    pairs=[];jobs=[]
    for repeat in (1,2):
        for t in tasks.TASKS:
            pair=t+'__r'+str(repeat);first=pair+'__first';pairs.append(dict(id=pair,task=t,first=first,arms=['regeneration','feedback']))
            jobs.append(dict(id=first,pair=pair,task=t,stage='first',arm='shared',prompt=runner.first_prompt(t)))
    for pair in pairs:
        for arm in pair['arms']:jobs.append(dict(id=pair['id']+'__'+arm,pair=pair['id'],task=pair['task'],stage='branch',arm=arm,depends_on=pair['first']))
    return dict(jobs=jobs,pairs=pairs,max_calls=24,model='gpt-5.6-sol',reasoning='low',api_timeout=180,wall_budget_seconds=5400,disk_budget_bytes=500*1024*1024,source_hashes=runner.hashes())

def main():
    run=BASE/'runs/control-tests-v1';assert not run.exists();run.mkdir(parents=True);plan=plan_fixture();calls=[];tests=[]
    refs={t:tasks.reference(t) for t in tasks.TASKS}
    def ok(args,folder,prompt):
        calls.append(folder);task=folder.parent.name.split('__')[0]
        return refs[task],dict(tools_used=False,usage=dict(input_tokens=10,output_tokens=20,cached_input_tokens=0,cache_write_input_tokens=0,reasoning_output_tokens=2),generation_seconds=0)
    def public(t,raw,rows,folder):
        assert rows==batch.read(runner.ASSETS/(t+'-public.json'))
        return dict(status='PASS',mismatches=[],scope='MOCK_PUBLIC')
    full=run/'complete';full.mkdir()
    with patch.object(runner.adapter,'generate_text',side_effect=AssertionError('Real network forbidden')):
        result=runner.campaign(full,plan,ok,public);assert result['status']=='GENERATION_COMPLETE' and len(calls)==24
        runner.campaign(full,plan,ok,public);assert len(calls)==24
        tests+=['24 unique cap','completed calls never repeated']
        # Same candidate/common instruction; only public execution JSON is added.
        original=batch.read
        def guarded_read(path):
            assert '-private.json' not in str(path),'Hidden read during prompt construction'
            return original(path)
        with patch.object(batch,'read',side_effect=guarded_read),patch.object(tasks,'reference',side_effect=AssertionError('Reference forbidden')):
            for t in tasks.TASKS:
                a=runner.branch_prompt(t,refs[t]);fb=dict(status='FUNCTION_FAIL',mismatches=[])
                b=runner.branch_prompt(t,refs[t],fb)
                from fsm_study import NO_TOOLS
                assert b==a[:-len(NO_TOOLS)]+'Public execution results:\n'+json.dumps(fb,separators=(',',':'))+'\n'+NO_TOOLS
        tests+=['public-only prompts','identical branch facts/candidate/instruction']
        api=run/'api';api.mkdir();count=0
        def fail(args,folder,prompt):
            nonlocal count
            count+=1;raise lab.LabError('API_ERROR','mock','No actual request')
        assert runner.campaign(api,plan,fail,public)['status']=='STOPPED_INFRASTRUCTURE' and count==1
        runner.campaign(api,plan,ok,public);assert len(calls)==24
        tests+=['API failure stops without retry']
        unknown=run/'unknown';p=unknown/'jobs'/plan['jobs'][0]['id'];p.mkdir(parents=True);batch.atomic(p/'started.json',dict(reserved_calls=1))
        assert runner.campaign(unknown,plan,ok,public)['status']=='STOPPED_INFRASTRUCTURE' and len(calls)==24
        tests+=['unknown interrupted reservation never reissued']
        fifth=run/'fifth';fifth.mkdir();fcount=0
        def fifth_error(args,folder,prompt):
            nonlocal fcount
            fcount+=1
            if fcount==5:raise lab.LabError('API_ERROR','mock','Fifth synthetic failure')
            return ok(args,folder,prompt)
        assert runner.campaign(fifth,plan,fifth_error,public)['status']=='STOPPED_INFRASTRUCTURE' and fcount==5 and batch.read(fifth/'gate.json')['passed']
        tests+=['four-service-only gate and stop fifth error']
        for name,changes in [('zero_calls',dict(max_calls=0)),('disk',dict(disk_budget_bytes=0)),('wall',dict(wall_budget_seconds=-1))]:
            folder=run/name;folder.mkdir();p=dict(plan,**changes);before=len(calls)
            assert runner.campaign(folder,p,ok,public)['status']=='BUDGET_STOP' and len(calls)==before
        tests+=['call/disk/wall budget stops']
        source=run/'source';source.mkdir()
        with patch.object(runner,'hashes',return_value={'changed':'1'}):assert runner.campaign(source,plan,ok,public)['status']=='SOURCE_CHANGED'
        tests+=['source change stops before dispatch']
        # Invalid initial candidate is kept in all branch denominators.
        invalid=run/'invalid';invalid.mkdir();invcount=0
        def bad(args,folder,prompt):
            nonlocal invcount
            invcount+=1;return 'not valid RTL',dict(tools_used=False,usage=None)
        def invalidpublic(t,raw,rows,folder):return dict(status='RTL_REJECTED',mismatches=[])
        assert runner.campaign(invalid,plan,bad,invalidpublic)['status']=='GENERATION_COMPLETE' and invcount==24
        tests+=['invalid first candidates retained through both arms']
        with patch.object(judge,'simulate',return_value=dict(status='PASS',label='MOCK_JUDGE_NOT_SIMULATED')):runner.score(full,plan)
        summary=batch.read(full/'summary.json');assert summary['actual_unique_usage']['input_tokens']==240 and summary['arms']['feedback']['shared_first_plus_branch_usage']['input_tokens']==160 and summary['arms']['feedback']['half_shared_allocated_usage']['input_tokens']==120
        tests+=['shared cost actual/strategy/allocation bookkeeping']
        with batch.lock(full):runner.seal(full)
        assert 'run.lock' not in batch.read(full/'evidence-lock.json');tests+=['Windows-safe seal under active lock']
    batch.atomic(run/'summary.json',dict(status='PASS',model_calls=0,icarus_evaluations=0,mock_adapter_invocations=24+1+5+24,tests=tests,label='MOCK_ENGINEERING_ONLY'))
    batch.atomic(run/'source-lock.json',runner.hashes());runner.seal(run);print(tests)
if __name__=='__main__':main()
