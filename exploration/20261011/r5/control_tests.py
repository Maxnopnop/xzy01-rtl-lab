"""Offline callbacks, real Icarus judge. Not real model evidence."""
import json,sys
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import tasks,teacher,runner,judge
from calibrate_v3 import mutants
lab=runner.lab;batch=runner.batch;RUN=BASE/'runs/control-v1'
def main():
    assert not RUN.exists();RUN.mkdir(parents=True);p=runner.plan();batch.atomic(RUN/'fixture-plan.json',p);calls=[];refs={t:(BASE/'references'/f'{t}.sv').read_text() for t in tasks.TASKS}
    def fixture(args,folder,prompt):
        jid=folder.parent.name;j=next(x for x in p['jobs'] if x['id']==jid);task=j['task'];calls.append(jid)
        if j['role']=='intent':raw='{' if task=='phase_snapshot' and 'r1' in jid else json.dumps(teacher.contract(task))
        else:
            raw=refs[task]
            if j['role']=='first_rtl' and task=='phase_snapshot' and 'r1' in jid:raw='```verilog\n'+raw+'\n```\n```verilog\n'+raw+'\n```'
            if j['role']=='direct_second' and task=='phase_snapshot' and 'r2' in jid:raw='module phase_snapshot(input clk); broken syntax; endmodule'
            bad=(task=='phase_snapshot' and 'r1__structured__regeneration' in jid or task=='escape_frame' and 'r1__direct__feedback' in jid or task=='masked_ring_alloc' and ('r2__structured__regeneration' in jid or 'r2__direct__feedback' in jid))
            if bad:raw=mutants(task,raw)
        (folder/'fixture-response.txt').write_text(raw);return raw,dict(tools_used=False,stage='REALISTIC_GENERATION_FIELD',usage=dict(input_tokens=100,output_tokens=20,cached_input_tokens=0,cache_write_input_tokens=0,reasoning_output_tokens=3),source='OFFLINE_MOCK')
    def public(task,rtl,rows,folder):
        assert not list((RUN/'full/jobs').glob('*/hidden-judge.json'))
        assert rows==batch.read(runner.ASSETS/f'{task}-public.json')
        r=judge.public_feedback(task,rtl,rows,folder);assert 'intent_spec' not in r and 'rtl_intent' not in r;return r
    with patch.object(runner.adapter,'generate_text',side_effect=AssertionError('Real CLI generation forbidden')):
        dispatch=runner.campaign(RUN/'full',p,fixture,public);assert dispatch['status']=='GENERATION_COMPLETE';batch.atomic(RUN/'full/dispatch.json',dispatch)
        assert len(calls)==48 and len(set(calls))==48
        summary=runner.score(RUN/'full',p);rows=batch.read(RUN/'full/results.json')
        assert summary['started']==48 and all(s['denominator']==6 and s['opportunities']==18 and s['allocated_calls']==12 for s in summary['strategies'].values())
        assert summary['actual_unique_usage']['input_tokens']==4800
        assert sum(s['shared_half_usage']['input_tokens'] for s in summary['strategies'].values())==4800
        assert summary['effects']==dict(help=2,harm=2,no_change=8),summary['effects']
        assert summary['role_statuses']['intent']['EXTRACTION_ERROR']==1 and summary['role_statuses']['first_rtl']['EXTRACTION_ERROR']==1
        assert all(r['role'] in ('intent','first_rtl','direct_first','direct_second','branch') for r in rows)
        # D2 stays parent even when D1 passes and D2 fails. No best-of or implicit score selection.
        jid='phase_snapshot__r2__direct__feedback';parent='phase_snapshot__r2__direct__second'
        prompt=(RUN/'full/jobs'/jid/'call/exact-prompt.txt').read_text();assert runner.raw(RUN/'full',parent) in prompt
        for j in p['jobs']:
            if j['role']!='branch':continue
            f=RUN/'full/jobs'/j['id']/'call/exact-prompt.txt';candidate=runner.raw(RUN/'full',j['first_id']);fb=batch.read(RUN/'full/jobs'/j['first_id']/'public-feedback.json')
            assert f.read_bytes()==runner.prompts.branch(j['task'],j['representation'],None,candidate,fb if j['arm']=='feedback' else None).encode()
            assert 'IR_spec' not in f.read_text() and 'RTL_intent' not in f.read_text()
        # Resume after completion: no re-generation or public/hidden re-evaluation.
        assert runner.campaign(RUN/'full',p,lambda *a:(_ for _ in ()).throw(AssertionError('resend')),public)['status']=='GENERATION_COMPLETE'
        assert runner.score(RUN/'full',p)==summary
        # Unknown reservation stops immediately, retains fixed denominators/pending slots.
        run=RUN/'unknown';folder=run/'jobs'/p['jobs'][0]['id'];folder.mkdir(parents=True);batch.atomic(folder/'started.json',dict(utc=lab.utc()))
        def forbidden(*a):raise AssertionError('must not resend')
        assert runner.campaign(run,p,forbidden)['status']=='STOPPED_INFRASTRUCTURE';u=runner.score(run,p);assert u['started']==1 and u['statuses']==dict(UNKNOWN_INTERRUPTED=1,PENDING=47);assert all(v['denominator']==6 for v in u['strategies'].values())
        # Infrastructure generation failure is reserved once and never retried.
        run=RUN/'api-error';attempts=[]
        def failure(*a):attempts.append(1);raise lab.LabError('API_ERROR','fixture','Offline deliberate failure, not403')
        assert runner.campaign(run,p,failure)['status']=='STOPPED_INFRASTRUCTURE';assert runner.campaign(run,p,forbidden)['status']=='STOPPED_INFRASTRUCTURE';assert len(attempts)==1;runner.score(run,p)
        # Byte limit is predispatch, no reservation/model callback.
        run=RUN/'input-limit';g=runner.generate(run,dict(id='limit'),p,'x'*(256*1024+1),forbidden);assert g['status']=='INPUT_LIMIT' and not g['model_called'] and not list(run.glob('jobs/*/started.json'))
        # Real extraction policy for multiblock and exact byte boundary in new-task module.
        boundary=[];sv=refs['phase_snapshot']
        for unicode in (False,True):
            for size in (131071,131072,131073):
                header=sv+'\n//';remaining=size-len(header.encode());text=header+('中'*(remaining//3)+'x'*(remaining%3) if unicode else 'x'*remaining)
                assert len(text.encode())==size
                try:lab.extract_rtl(text,'phase_snapshot');status='PASS'
                except lab.LabError as e:status=e.status
                assert status==('EXTRACTION_ERROR' if size>131072 else 'PASS');boundary.append(dict(unicode=unicode,bytes=size,status=status))
    batch.atomic(RUN/'boundary.json',boundary);batch.atomic(RUN/'source-lock.json',runner.hashes());batch.atomic(RUN/'summary.json',dict(status='PASS',label='OFFLINE MOCK+REAL JUDGE ONLY',real_model_calls=0,fixture_calls=len(calls),effects=summary['effects'],groups=['48stages','role/judge fields','S invalid IR retained','multiblock branches','D2 unconditional parent','spec-only shared feedback','hidden after dispatch','fixed denominators/accounting','unknown no resend','api error no resend','input byte cap','ASCII UTF8 extraction boundary'],shared_allocation_total=48,descendant_tree='UNVERIFIED'))
    runner.seal(RUN);print('CONTROL_PASS; 48 offline callbacks; 0 real models')
if __name__=='__main__':main()
