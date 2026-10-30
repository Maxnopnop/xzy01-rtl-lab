"""Real extraction/backend fields, mocked generation. Zero model calls."""
import sys,json,re,time
from pathlib import Path
from unittest.mock import patch
from collections import Counter
BASE=Path(__file__).resolve().parent;OLD=BASE.parent/'r3';ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(OLD),str(ROOT)]
import runner,judge,tasks,batch,rtl_lab as lab

def preserved():
    records={}
    parent=BASE.parent
    runs=[parent/'runs'/n for n in ('compound-v1','delayed-v1','factorial20-v1','formal-v1','r1b-v1','r1b-v2','timed-reset-v1','timed-calibration-v1','timed-calibration-v2','r2-prepared-v1')]
    runs+=[OLD/'runs'/n for n in ('calibration-v1','control-tests-v1','prepared-v1')]
    for run in runs:
        for rel,h in batch.read(run/'evidence-lock.json').items():
            p=run/rel;assert lab.digest(p.read_bytes())==h;records[str(p.relative_to(ROOT))]=h
        plan=run/'plan.json';sources=batch.read(plan).get('source_hashes',{}) if plan.exists() else batch.read(run/'source-lock.json')
        for rel,h in sources.items():assert lab.digest((ROOT/rel).read_bytes())==h;records[rel]=h
    for rel,h in batch.read(OLD/'assets-v1/lock.json').items():
        p=OLD/'assets-v1'/rel;assert lab.digest(p.read_bytes())==h;records[str(p.relative_to(ROOT))]=h
    return records

def padded(raw,target,unicode=False):
    # Exact UTF-8 byte lengths; padding is a harmless block comment.
    overhead=len(('/*'+'*/\n'+raw).encode());n=target-overhead;assert n>=0
    padding=('中'*(n//3)+' '*(n%3)) if unicode else ' '*n
    result='/*'+padding+'*/\n'+raw;assert len(result.encode())==target;return result

def fixture_plan():
    pairs=[];jobs=[]
    for repeat in (1,2):
        for t in tasks.TASKS:
            pair=t+'__r'+str(repeat);first=pair+'__first';pairs.append(dict(id=pair,task=t,first=first,arms=['regeneration','feedback']))
            jobs.append(dict(id=first,pair=pair,task=t,role='first',arm='shared',prompt=runner.first_prompt(t)))
    for p in pairs:
        for arm in p['arms']:jobs.append(dict(id=p['id']+'__'+arm,pair=p['id'],task=p['task'],role='branch',arm=arm,depends_on=p['first']))
    return dict(jobs=jobs,pairs=pairs,max_calls=24,model='MOCK_NOT_A_MODEL',reasoning='low',api_timeout=180,wall_budget_seconds=5400,disk_budget_bytes=100*1024*1024,source_hashes=runner.hashes())

def main():
    run=BASE/'runs/acceptance-v1';assert not run.exists();run.mkdir(parents=True);start=time.monotonic();before=preserved();batch.atomic(run/'old-preservation-before.json',before)
    batch.atomic(run/'source-lock.json',runner.hashes());tests=[];boundary=[];refs={t:tasks.reference(t) for t in tasks.TASKS}
    task='cancel_deadline';rows=batch.read(runner.ASSETS/(task+'-public.json'))
    calls=[]
    with patch.object(runner.adapter,'generate_text',side_effect=AssertionError('Network generation forbidden')):
        for unicode in (False,True):
            for size in (131071,131072,131073):
                label=('utf8' if unicode else 'ascii')+'_'+str(size);raw=padded(refs[task],size,unicode)
                (run/(label+'.txt')).write_bytes(raw.encode());result=judge.simulate(run/'boundary'/label,task,raw,rows)
                expected='EXTRACTION_ERROR' if size>131072 else 'PASS';assert result['status']==expected,(label,result)
                if expected=='EXTRACTION_ERROR':assert not (run/'boundary'/label/'compile.json').exists()
                boundary.append(dict(label=label,bytes=len(raw.encode()),expected=expected,result=result))
        tests.append('ASCII/UTF8 raw byte thresholds: below/equal accepted, above extraction failure')
        plan=fixture_plan();batch.atomic(run/'fixture-plan.json',plan);payloads={};expectfirst=[]
        for i,p in enumerate(plan['pairs']):
            ref=refs[p['task']];multi='```systemverilog\n'+ref+'```\n```systemverilog\n'+ref+'```'
            raw=multi if i==0 else padded(ref,131073,i==2) if i in (1,2) else padded(ref,131072,i==4) if i in (3,4) else padded(ref,131071,i==6) if i in (5,6) else ref
            payloads[p['first']]=raw;expectfirst.append('EXTRACTION_ERROR' if i<3 else 'PASS')
            payloads[p['id']+'__regeneration']=multi if i==1 else ref.replace('owner<=1;','owner<= ;') if i==3 else ref
            payloads[p['id']+'__feedback']=multi if i==0 else ref.replace('remaining<=3','remaining<=2') if i==4 else ref
        batch.atomic(run/'payloads.json',payloads)
        def supply(args,folder,prompt):
            jid=folder.parent.name;calls.append(jid)
            return payloads[jid],dict(tools_used=False,usage=dict(input_tokens=100,output_tokens=20,cached_input_tokens=0,cache_write_input_tokens=0,reasoning_output_tokens=0),generation_seconds=0,label='OFFLINE_FIXTURE')
        full=run/'full-flow';full.mkdir()
        original=batch.read
        def public_only(path):
            assert '-private.json' not in str(path),'Private data read during candidate/branch generation'
            return original(path)
        with patch.object(batch,'read',side_effect=public_only):dispatch=runner.campaign(full,plan,supply)
        assert dispatch['status']=='GENERATION_COMPLETE' and len(calls)==len(set(calls))==24
        for p,expected in zip(plan['pairs'],expectfirst):
            assert batch.read(full/'jobs'/p['first']/'public-feedback.json')['status']==expected
            assert all((full/'jobs'/(p['id']+'__'+a)/'generation.json').exists() for a in p['arms'])
            candidate=(full/'jobs'/p['first']/'response.txt').read_text(encoding='utf-8');a=(full/'jobs'/(p['id']+'__regeneration')/'call/exact-prompt.txt').read_text(encoding='utf-8');b=(full/'jobs'/(p['id']+'__feedback')/'call/exact-prompt.txt').read_text(encoding='utf-8')
            assert candidate in a and candidate in b
            from fsm_study import NO_TOOLS
            feedback=batch.read(full/'jobs'/p['first']/'public-feedback.json')
            assert b==a[:-len(NO_TOOLS)]+'Public execution results:\n'+json.dumps(feedback,separators=(',',':'))+'\n'+NO_TOOLS
        tests+=['Actual multi-block/oversize firsts retained in both arms, full raw input preserved','Public-only branch construction and feedback-only prompt difference']
        runner.score(full,plan);out=batch.read(full/'results.json');summary=batch.read(full/'summary.json')
        for j,row in zip(plan['jobs'],out):
            assert row['role']==j['role'] and row['id']==j['id'] and row['arm']==j['arm']
            assert 'stage' not in row and row['judge']['stage'] in ('simulate','compile','extraction')
            assert row['status']==row['judge']['status']
        assert summary['first_candidate_statuses']==dict(EXTRACTION_ERROR=3,PASS=5)
        assert summary['statuses']==dict(EXTRACTION_ERROR=5,PASS=17,COMPILE_FAIL=1,FUNCTION_FAIL=1)
        assert summary['effects']==dict(harm=2,help=2,no_change=4)
        assert summary['actual_unique_usage']['input_tokens']==2400 and all(a['half_shared_allocated_usage']['input_tokens']==1200 for a in summary['arms'].values())
        tests+=['Real simulate/compile/extraction judge fields isolated from role','Extraction errors classified in paired functional denominator','Shared cost arithmetic preserves role classification']
        runner.campaign(full,plan,supply);assert len(calls)==24;tests.append('Completed workflow does not resend any slot')
        with batch.lock(full):runner.seal(full)
        assert 'run.lock' not in batch.read(full/'evidence-lock.json');tests.append('Complete real-field workflow seals under Windows lock')
        api=run/'api-error';api.mkdir();apicount=0
        def api_error(args,folder,prompt):
            nonlocal apicount
            apicount+=1;raise lab.LabError('API_ERROR','offline_mock','Synthetic; no request sent')
        assert runner.campaign(api,plan,api_error)['status']=='STOPPED_INFRASTRUCTURE'
        assert runner.campaign(api,plan,api_error)['status']=='STOPPED_INFRASTRUCTURE' and apicount==1
        unknown=run/'unknown';p=unknown/'jobs'/plan['jobs'][0]['id'];p.mkdir(parents=True);batch.atomic(p/'started.json',dict(reserved_calls=1))
        assert runner.campaign(unknown,plan,supply)['status']=='STOPPED_INFRASTRUCTURE' and len(calls)==24
        tests+=['API stop and no retry','Unknown reservation not reissued']
        for name,config in [('call-cap',dict(max_calls=0)),('disk-cap',dict(disk_budget_bytes=0)),('wall-cap',dict(wall_budget_seconds=-1))]:
            path=run/name;path.mkdir();assert runner.campaign(path,dict(plan,**config),supply)['status']=='BUDGET_STOP' and len(calls)==24
        path=run/'source-change';path.mkdir()
        with patch.object(runner,'hashes',return_value={}):assert runner.campaign(path,plan,supply)['status']=='SOURCE_CHANGED'
        tests.append('Budget/source failures stop before generation')
    after=preserved();assert before==after
    compiles=list(run.rglob('compile.json'));sims=list(run.rglob('simulate.json'));receiptcount=0
    for p in sims:
        proc=batch.read(p);assert proc['returncode']==0 and not proc['timeout'] and not proc['output_limit']
        receipt=(p.parent/'verdict.txt').read_text().strip();assert re.fullmatch(r'RTL_LAB_V1 [a-f0-9]+ checks=\d+ errors=\d+',receipt);receiptcount+=1
    for p in compiles:
        proc=batch.read(p);assert not proc['timeout'] and not proc['output_limit']
    batch.atomic(run/'boundary-results.json',boundary)
    batch.atomic(run/'summary.json',dict(status='PASS',real_model_calls=0,mock_adapter_invocations=25,tests=tests,boundary_cases=len(boundary),real_compile_evaluations=len(compiles),real_simulator_receipts=receiptcount,
                engineering_fixture_statuses=summary['statuses'],engineering_pair_effects=summary['effects'],old_preserved_files=len(before),elapsed_seconds=time.monotonic()-start,label='ENGINEERING_ONLY; fixtures are not model results'))
    runner.seal(run);print(json.dumps(batch.read(run/'summary.json'),indent=2))
if __name__=='__main__':main()
