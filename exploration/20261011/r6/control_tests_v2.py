"""Synthetic scheduling controls, no real model or extra simulation."""
import copy,json
from pathlib import Path
import runner,teacher,stream_process as s
BASE=Path(__file__).resolve().parent;RUN=BASE/'runs/control-v2';assert not RUN.exists();RUN.mkdir(parents=True)
p=runner.plan();calls=[]
def mock(args,folder,prompt):
    job=folder.parent.name;task=job.split('__')[0];calls.append(job)
    text=teacher.make(task) if job.endswith('__intent') else (BASE/'references'/(task+'.sv')).read_text()
    if job=='ordered_retire__r1__structured__first':text='```verilog\n'+text+'\n```\n```verilog\n'+text+'\n```'
    (folder/'model_output.raw.txt').write_bytes(text.encode());s.atomic(folder/'mock-receipt.json',dict(label='ARTIFICIAL_NOT_LLM',job=job,prompt_sha256=s.digest(prompt.encode())))
    return text,dict(tools_used=False,usage=dict(input_tokens=10,output_tokens=2,cached_input_tokens=3,cache_write_input_tokens=0,reasoning_output_tokens=1))
def public(task,raw,rows,folder):
    if raw.count('```')>2:return runner.judge.public_feedback(task,raw,rows,folder)
    return dict(status='PASS',stage='simulation',mismatches=[],label='MOCK disclosed RTL_spec only')
try:
    result=runner.campaign(RUN,p,call=mock,feedback=public)
    assert result['status']=='GENERATION_COMPLETE' and len(calls)==len(set(calls))==48
    # Score namespace control; real checker fields/format tested in calibration-v1.
    def simulated(folder,task,raw,rows):
        if raw.count('```')>2:return original(folder,task,raw,rows)
        return dict(status='PASS',stage='simulation',checks=len(rows))
    original=runner.judge.simulate;runner.judge.simulate=simulated
    summary=runner.score(RUN,p);runner.judge.simulate=original
    assert all(v['denominator']==6 and v['opportunities']==18 and v['allocated_calls']==12 for v in summary['strategies'].values())
    assert summary['started']==48 and summary['actual_unique_usage']['input_tokens']==480
    assert sum(v['shared_half_usage']['input_tokens'] for v in summary['strategies'].values())==480
    rows=s.read(RUN/'results.json');assert all(r['role']==j['role'] for r,j in zip(rows,p['jobs']))
    bad=next(r for r in rows if r['id']=='ordered_retire__r1__structured__first');assert bad['status']=='EXTRACTION_ERROR'
    assert all(next(r for r in rows if r['id']=='ordered_retire__r1__structured__'+arm)['status']=='PASS' for arm in ['feedback','regeneration'])
    # INPUT_LIMIT: no dispatch, fixed slot retained. Exact 256KiB accepted.
    j=p['jobs'][0];small=BASE/'runs/control-boundaries-v2';small.mkdir()
    exact=runner.generate(small,j,p,'x'*(256*1024),mock);assert exact['status']=='GENERATED'
    j2=copy.deepcopy(j);j2['id']+='__over';over=runner.generate(small,j2,p,'x'*(256*1024+1),mock);assert over['status']=='INPUT_LIMIT' and not over['model_called']
    for name,raw in [('multi','```verilog\nmodule restoring_divide;endmodule\n```\n```verilog\nmodule restoring_divide;endmodule\n```'),('over','x'*(128*1024+1))]:
        q=BASE/'runs'/('extraction-'+name+'-v2');q.mkdir();r=original(q,'restoring_divide',raw,s.read(BASE/'assets/restoring_divide-public.json'));assert r['status']=='EXTRACTION_ERROR';s.atomic(q/'receipt.json',r)
    s.atomic(RUN/'control-audit.json',dict(status='PASS',label='SYNTHETIC_CONTROLS_NOT_MODEL_EVIDENCE',calls=48,main_denominator=48,source_hashes=runner.hashes(),summary=summary))
except BaseException as e:s.atomic(RUN/'failure.json',dict(type=type(e).__name__,message=str(e)));raise
finally:
    runner.seal(RUN)
    for name in ['control-boundaries-v2','extraction-multi-v2','extraction-over-v2']:
        q=BASE/'runs'/name
        if q.exists() and not (q/'evidence-lock.json').exists():runner.seal(q)
print('Synthetic flow PASS; 48 mock returns, 2 input boundaries, 2 extraction boundaries; 0 model calls')
