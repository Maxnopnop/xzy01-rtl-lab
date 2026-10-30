"""Small full 48-slot offline fixture flow, real intent/RTL judge fields; not research scores."""
import sys,json,copy
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import runner,tasks,intent,prompts,calibration_contracts as contracts,batch,rtl_lab as lab
from fsm_study import NO_TOOLS
RUN=BASE/'runs/control-v1'
def main():
    assert not RUN.exists();RUN.mkdir(parents=True);p=runner.plan();batch.atomic(RUN/'fixture-plan.json',p);batch.atomic(RUN/'source-lock.json',runner.hashes())
    refs={t:(BASE/'references'/(t+'.sv')).read_text(encoding='utf-8') for t in tasks.TASKS};payloads={};calls=[]
    for j in p['jobs']:
        c=p['cases'].index(next(c for c in p['cases'] if c['id']==j['case']));rep=j['representation'];task=j['task'];ref=refs[task]
        if j['role']=='intent':
            program=contracts.contract(task)
            if c==0 and rep=='structured':raw='invalid JSON'
            elif c==2 and rep=='linear':
                next(iter(program['registers'].values()))['width']=9;raw=intent.serialize(program,rep)
            else:
                if c==1 and rep=='structured':program['timing']['reset']='sync_low'
                raw=intent.serialize(program,rep)
        else:
            raw=ref
            if c==0 and rep=='linear' and j['role']=='first_rtl':raw='```sv\n'+ref+'```\n```sv\n'+ref+'```'
            if c==0 and rep=='linear' and j['arm']=='regeneration':raw='not RTL'
            if c==1 and rep=='structured' and (j['role']=='first_rtl' or j['arm']=='regeneration'):raw=ref.replace('credit<=funded-cost','credit<=credit-cost')
            if c==1 and rep=='linear' and j['arm']=='feedback':raw=ref.replace('credit<=0','credit<= ;')
            if c==2 and rep=='structured' and j['arm']=='feedback':raw='not RTL'
        payloads[j['id']]=raw
    batch.atomic(RUN/'payloads.json',payloads)
    def supply(args,folder,prompt):
        jid=folder.parent.name;calls.append(jid)
        return payloads[jid],dict(tools_used=False,usage=dict(input_tokens=100,output_tokens=20,cached_input_tokens=10,cache_write_input_tokens=0,reasoning_output_tokens=1),generation_seconds=0,label='OFFLINE_FIXED_FIXTURE')
    full=RUN/'full-flow';full.mkdir();read=batch.read
    def public_only(path):
        assert '-private.json' not in str(path),'Private scoring data during generation';return read(path)
    with patch.object(batch,'read',side_effect=public_only):dispatch=runner.campaign(full,p,supply)
    assert dispatch['status']=='GENERATION_COMPLETE' and len(calls)==len(set(calls))==48;batch.atomic(full/'dispatch.json',dispatch)
    tests=['48 unique mock calls complete despite invalid/unsupported intentions and multi-block first RTL; real public judge fields', 'Public/private isolation during complete generation']
    for case in p['cases']:
        prefix=case['id'];structured=(full/'jobs'/(prefix+'__structured__intent')/'call/exact-prompt.txt').read_text(encoding='utf-8');linear=(full/'jobs'/(prefix+'__linear__intent')/'call/exact-prompt.txt').read_text(encoding='utf-8')
        assert structured.split('Produce an implementation')[0]==linear.split('Produce an implementation')[0]
        for rep in ('structured','linear'):
            a=(full/'jobs'/(prefix+'__'+rep+'__regeneration')/'call/exact-prompt.txt').read_bytes().decode();b=(full/'jobs'/(prefix+'__'+rep+'__feedback')/'call/exact-prompt.txt').read_bytes().decode();fb=read(full/'jobs'/(prefix+'__'+rep+'__first')/'public-feedback.json')
            assert b==a.removesuffix(NO_TOOLS)+'Public execution feedback:\n'+json.dumps(fb,separators=(',',':'))+'\n'+NO_TOOLS
            assert payloads[prefix+'__'+rep+'__intent'] in a and payloads[prefix+'__'+rep+'__first'] in a
    tests.append('Same representation facts; feedback-only branch delta; invalid raw candidates preserved')
    summary=runner.score(full,p);rows=read(full/'results.json')
    for j,r in zip(p['jobs'],rows):assert j['role']==r['role'] and j['case']==r['case'] and j['representation']==r['representation'] and 'stage' not in r
    assert summary['actual_unique_usage']['input_tokens']==4800
    assert sum(s['shared_half_usage']['input_tokens'] for s in summary['strategies'].values())==4800
    assert all(s['opportunities']==18 and s['allocated_calls']==12 and s['denominator']==6 for s in summary['strategies'].values())
    assert summary['effects']==dict(help=2,harm=2,no_change=8),summary['effects']
    assert summary['intent_statuses']==dict(EXTRACTION_ERROR=1,PASS=9,FUNCTION_FAIL=1,UNSUPPORTED=1),summary['intent_statuses']
    assert {v['stage'] for r in rows if r.get('judge') for k,v in r['judge'].items() if 'stage' in v}>={'intent','compile','simulate','extraction'}
    tests+=['Real intent/compile/simulate/extraction fields isolated from job role', 'Fixed 6-case strategy denominators and 48-unique/72-opportunity/half-shared cost arithmetic', 'Observable three-judge statuses and unassessable malformed intentions']
    assert runner.campaign(full,p,supply)['status']=='GENERATION_COMPLETE' and len(calls)==48
    with batch.lock(full):runner.seal(full)
    tests+=['Completed workflow never resends','Seal excludes Windows mutable lock while held']
    errors=[]
    for label,modify in [('calls',lambda q:q.update(max_calls=0)),('wall',lambda q:q.update(wall_budget_seconds=-1)),('disk',lambda q:q.update(disk_budget_bytes=0)),('sources',lambda q:q.update(source_hashes={}))]:
        folder=RUN/label;folder.mkdir();q=copy.deepcopy(p);modify(q);count=len(calls);result=runner.campaign(folder,q,supply);assert result['status'] in ('BUDGET_STOP','SOURCE_CHANGED') and len(calls)==count;batch.atomic(folder/'result.json',result);errors.append(result)
    tests.append('Call/wall/disk/source bounds stop before callback')
    unknown=RUN/'unknown';jf=unknown/'jobs'/p['jobs'][0]['id'];jf.mkdir(parents=True);batch.atomic(jf/'started.json',dict(reserved_calls=1));count=len(calls)
    result=runner.campaign(unknown,p,supply);assert result['status']=='STOPPED_INFRASTRUCTURE' and len(calls)==count;assert read(jf/'generation.json')['status']=='UNKNOWN_INTERRUPTED';batch.atomic(unknown/'result.json',result)
    api=RUN/'api';api.mkdir();api_calls=[]
    def fail(args,folder,prompt):api_calls.append(1);raise lab.LabError('API_ERROR','fixture','Offline API failure; no network')
    assert runner.campaign(api,p,fail)['status']=='STOPPED_INFRASTRUCTURE' and len(api_calls)==1
    assert runner.campaign(api,p,fail)['status']=='STOPPED_INFRASTRUCTURE' and len(api_calls)==1
    tests.append('API/unknown stops and no retry or slot resend')
    overflow=RUN/'input-limit';overflow.mkdir();q=copy.deepcopy(p);q['input_byte_limit']=1;count=len(calls);j=p['jobs'][0];g=runner.generate(overflow,j,q,j['prompt'],supply);assert g['status']=='INPUT_LIMIT' and len(calls)==count
    # Pure summary keeps pending/unknown failures in fixed planned denominator.
    pending=[{k:v for k,v in j.items() if k!='prompt'}|dict(status='PENDING',generation=None,judge=None) for j in p['jobs']];s=runner.summarize(pending,p);assert all(x['passes']==0 and x['denominator']==6 for x in s['strategies'].values());assert s['effects']==dict(inconclusive=12)
    batch.atomic(RUN/'pending-summary.json',s);tests.append('Input byte limit and pending/unknown fixed denominators')
    result=dict(status='PASS',real_model_calls=0,label='ENGINEERING_ONLY_NO_MODEL_SCORES',tests=tests,mock_adapter_calls=49,full_mock_slots=48,compile_evaluations=len(list(full.rglob('compile.json'))),simulator_receipts=len(list(full.rglob('simulate.json'))),fixture_effects=summary['effects'])
    batch.atomic(RUN/'summary.json',result);runner.seal(RUN);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
