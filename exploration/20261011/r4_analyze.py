"""Read-only actual R4 audit/analysis; never generates or re-simulates RTL. Outputs outside run."""
import sys,json,re
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent;BASE=HERE/'r4';ROOT=HERE.parents[1]
sys.path[:0]=[str(BASE),str(ROOT)]
import runner_v2 as runner,batch,rtl_lab as lab,intent,prompts,tasks
RUN=runner.RUN
def main():
    assert (RUN/'dispatch.json').exists() and (RUN/'evidence-lock.json').exists(),'Wait for original campaign/hidden grading/seal'
    plan=runner.verify();lock=batch.read(RUN/'evidence-lock.json')
    assert set(lock)=={str(p.relative_to(RUN)) for p in RUN.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')}
    for rel,h in lock.items():assert lab.digest((RUN/rel).read_bytes())==h,rel
    rows=batch.read(RUN/'results.json');summary=batch.read(RUN/'summary.json');assert len(rows)==len(plan['jobs'])==48
    cache={};receipts=0;compiles=0;event_bindings=0;cli=[];infrastructure=[]
    def contract(jid,rep,task,split):
        key=(jid,split)
        if key not in cache:
            data=runner.raw(RUN,jid);rr=batch.read(runner.ASSETS/(task+'-'+split+'.json'));cache[key]=intent.check(data,rep,task,rr)
        return cache[key]
    def check_sim(folder,task,expected_rows,status):
        nonlocal receipts,compiles,event_bindings
        cf=folder/'compile.json'
        if not cf.exists():assert status in ('EXTRACTION_ERROR','RTL_REJECTED');return
        c=batch.read(cf);compiles+=1
        if status=='COMPILE_FAIL':assert c['returncode']!=0 and not c['timeout'];return
        if status not in ('PASS','FUNCTION_FAIL'):return
        s=batch.read(folder/'simulate.json');assert s['returncode']==0 and not s['timeout'] and not s['output_limit']
        m=re.fullmatch(r'RTL_LAB_V1 ([0-9a-f]+) checks=(\d+) errors=(\d+)',(folder/'verdict.txt').read_text().strip())
        assert m and '+nonce='+m[1] in s['command'] and int(m[2])==len(expected_rows)
        assert (int(m[3])==0)==(status=='PASS');receipts+=1
        iw=sum(w for n,w in tasks.TASKS[task]['inputs']);ow=sum(w for n,w in tasks.TASKS[task]['outputs'])
        words=[int(x,16) for x in (folder/'vectors.hex').read_text().splitlines()];assert len(words)==len(expected_rows)
        for word,event in zip(words,expected_rows):
            assert word&((1<<ow)-1)==event['expected'];packed=word>>ow
            assert packed&((1<<iw)-1)==event['input'] and (packed>>iw)&1==event['rst_n'] and (packed>>iw)>>1==event['clk']
        event_bindings+=len(words)
    for j,r in zip(plan['jobs'],rows):
        assert all(j[k]==r[k] for k in ('id','role','representation','arm','case','task')) and 'stage' not in r
        folder=RUN/'jobs'/j['id'];gen=r.get('generation')
        if gen is None:assert r['status']=='PENDING' and not (folder/'started.json').exists();continue
        assert gen==batch.read(folder/'generation.json')
        if gen['status']!='GENERATED':infrastructure.append(dict(id=j['id'],generation_status=gen['status']));continue
        assert (folder/'started.json').exists();raw=runner.raw(RUN,j['id']);call=folder/'call';prompt=(call/'exact-prompt.txt').read_bytes().decode('utf-8')
        assert lab.digest(prompt.encode())==gen['prompt_sha256'] and gen['prompt_bytes']==len(prompt.encode())
        if j['role']=='intent':assert prompt==j['prompt']
        elif j['role']=='first_rtl':assert prompt==prompts.first(j['task'],j['representation'],runner.raw(RUN,j['intent_id']))
        else:
            feedback=batch.read(RUN/'jobs'/j['first_id']/'public-feedback.json') if j['arm']=='feedback' else None
            assert prompt==prompts.branch(j['task'],j['representation'],runner.raw(RUN,j['intent_id']),runner.raw(RUN,j['first_id']),feedback)
        req=batch.read(call/'codex_request.json');process=batch.read(call/'codex.json')
        assert req['prompt']==prompt and (call/'codex_prompt.txt').read_bytes()==prompt.encode()
        assert req['prompt_bytes']==len(prompt.encode()) and req['prompt_sha256']==gen['prompt_sha256']
        assert req['requested_model']==plan['model'] and req['reasoning_effort']==plan['reasoning']
        adapter_rel=str((runner.V3/'cli_adapter.py').relative_to(ROOT));assert req['adapter_sha256']==plan['source_hashes'][adapter_rel]
        assert process['command'][-1]=='-' and '--model' in process['command'] and process['command'][process['command'].index('--model')+1]==plan['model']
        assert process['returncode']==0 and not process['timeout'] and not process['output_limit']
        assert batch.read(call/'codex_version.json')['returncode']==0 and batch.read(call/'codex_auth.json')['returncode']==0
        events=[json.loads(x) for x in (call/'codex.stdout.log').read_text(encoding='utf-8').splitlines() if x.strip()]
        completed=[e for e in events if e.get('type')=='turn.completed'];assert completed and completed[-1].get('usage')==gen['usage']
        assert not any(e.get('type') in ('error','turn.failed') for e in events)
        itemtypes={e.get('item',{}).get('type') for e in events if e.get('type','').startswith('item.')};assert itemtypes<={'agent_message','reasoning'} and gen['tools_used'] is False
        final=(call/'model_output.raw.txt').read_bytes();assert final.decode('utf-8').replace('\r\n','\n').replace('\r','\n')==raw
        thread=next(e['thread_id'] for e in events if e.get('type')=='thread.started');assert thread==gen['codex_thread_id']
        cli.append(dict(id=j['id'],thread_id=thread,version=(call/'codex_version.stdout.log').read_text().strip(),exe_sha256=req['codex_executable_sha256'],events_sha256=lab.digest((call/'codex.stdout.log').read_bytes()),final_raw_sha256=lab.digest(final),response_sha256=gen['response_sha256'],prompt_sha256=gen['prompt_sha256'],prompt_bytes=gen['prompt_bytes'],usage=gen['usage'],item_types=sorted(itemtypes),transport=req['prompt_transport']))
        private=batch.read(runner.ASSETS/(j['task']+'-private.json'));judged=r['judge']
        irid=j['id'] if j['role']=='intent' else j['intent_id'];ir,values=contract(irid,j['representation'],j['task'],'private')
        assert judged['intent_spec']==ir
        if j['role']!='intent':
            check_sim(folder/'hidden-spec',j['task'],private,judged['rtl_spec']['status'])
            if values is None:assert judged['rtl_intent']['status']=='NOT_ASSESSABLE'
            else:check_sim(folder/'hidden-intent',j['task'],[dict(e,expected=v) for e,v in zip(private,values)],judged['rtl_intent']['status'])
            for sub in ('hidden-spec','hidden-intent'):
                f=folder/sub
                if (f/'dut.sv').exists():assert (f/'dut.sv').read_bytes()==lab.extract_rtl(raw,tasks.TASKS[j['task']]['module']).encode()
        if j['role']=='first_rtl' and (folder/'public-feedback.json').exists():
            public=batch.read(runner.ASSETS/(j['task']+'-public.json'));fb=batch.read(folder/'public-feedback.json');irpub,publicvalues=contract(irid,j['representation'],j['task'],'public');assert fb['intent_spec']==irpub
            check_sim(folder/'public/rtl-spec',j['task'],public,fb['rtl_spec']['status'])
            if publicvalues is None:assert fb['rtl_intent']['status']=='NOT_ASSESSABLE'
            else:check_sim(folder/'public/rtl-intent',j['task'],[dict(e,expected=v) for e,v in zip(public,publicvalues)],fb['rtl_intent']['status'])
    assert runner.summarize(rows,plan)==summary
    assert len({r['thread_id'] for r in cli})==len(cli)
    prior=batch.read(BASE/'prior-bindings.json')
    for rel,h in prior.items():assert lab.digest((ROOT/rel).read_bytes())==h
    # Explicit actual reserved/generation ledger distinct from planned shared opportunities.
    usage_keys=('input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens')
    def usage(group):return {k:sum((r['generation'].get('usage') or {})[k] for r in group) if group and all(isinstance(((r.get('generation') or {}).get('usage') or {}).get(k),(int,float)) for r in group) else None for k in usage_keys}
    ledger={}
    for rep in ('structured','linear'):
        shared=[r for r in rows if r['representation']==rep and r['arm']=='shared' and r.get('generation')];shared_u=usage(shared)
        for arm in ('regeneration','feedback'):
            branch=[r for r in rows if r['representation']==rep and r['arm']==arm and r.get('generation')];bu=usage(branch)
            ledger[rep+'_'+arm]=dict(planned_opportunities=18,planned_half_shared_calls=12,actual_reserved_full=len([r for r in shared+branch if (RUN/'jobs'/r['id']/'started.json').exists()]),actual_reserved_half=len([r for r in shared if (RUN/'jobs'/r['id']/'started.json').exists()])/2+len([r for r in branch if (RUN/'jobs'/r['id']/'started.json').exists()]),shared_usage=shared_u,branch_usage=bu,half_shared_usage={k:shared_u[k]/2+bu[k] if shared_u[k] is not None and bu[k] is not None else None for k in usage_keys})
    by_family={t:[x for x in summary['comparisons'] if x['case'].startswith(t+'__')] for t in tasks.TASKS}
    representation=[]
    for arm in ('regeneration','feedback'):
        for case in plan['cases']:
            rr={r['representation']:r['status'] for r in rows if r['role']=='branch' and r['arm']==arm and r['case']==case['id']};a=rr['linear'];b=rr['structured']
            effect='inconclusive' if a not in runner.FUNCTIONAL or b not in runner.FUNCTIONAL else 'structured_only_pass' if a!='PASS' and b=='PASS' else 'linear_only_pass' if a=='PASS' and b!='PASS' else 'same_pass_status'
            representation.append(dict(case=case['id'],arm=arm,linear=a,structured=b,effect=effect))
    valid_ir={r['id']:r['status']=='PASS' or r['status']=='FUNCTION_FAIL' for r in rows if r['role']=='intent'}
    conditional={}
    for rep in ('structured','linear'):
        for arm in ('regeneration','feedback'):
            subset=[r for r in rows if r['role']=='branch' and r['representation']==rep and r['arm']==arm and valid_ir.get(r['intent_id'],False)]
            conditional[rep+'_'+arm]=dict(denominator=len(subset),passes=sum(r['status']=='PASS' for r in subset),label='Sensitivity only; does not replace fixed6')
    output=dict(status='PASS',checked_utc=lab.utc(),plan_sha256=batch.read(RUN/'plan-lock.json')['sha256'],dispatch=batch.read(RUN/'dispatch.json'),sealed_files=len(lock),source_files=len(plan['source_hashes']),prior_preserved_bindings=len(prior),planned_slots=48,reserved=len(list((RUN/'jobs').glob('*/started.json'))),generated=len(cli),pending=sum(r['status']=='PENDING' for r in rows),statuses=summary['statuses'],intent_statuses=summary['intent_statuses'],first_rtl_statuses=summary['first_rtl_statuses'],strategies=summary['strategies'],feedback_effects=summary['effects'],family_feedback=by_family,representation_comparisons=representation,actual_unique_usage=summary['actual_unique_usage'],actual_ledger=ledger,conditional_parseable_sensitivity=conditional,observations=summary['observations'],compile_evaluations=compiles,simulator_receipts=receipts,bound_event_rows=event_bindings,cli_receipts=cli,infrastructure=infrastructure,adapter_wall_seconds=sum((r.get('generation') or {}).get('elapsed_seconds',0) for r in rows),model_exec_seconds=sum((r.get('generation') or {}).get('generation_seconds',0) for r in rows),campaign_to_scoring_seconds=(RUN/'results.json').stat().st_mtime-batch.read(RUN/'dispatch-start.json')['epoch'],run_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()),fees='UNKNOWN',limits='Controlled JSON vs controlled linear organization only; matching call opportunities not tokens; observable agreement not internal reasoning attribution; development mechanisms, finite binary events, common-author references')
    batch.atomic(BASE/'actual-analysis.json',output);print(json.dumps({k:v for k,v in output.items() if k not in ('cli_receipts','observations','family_feedback','representation_comparisons','actual_ledger','strategies')},indent=2))
if __name__=='__main__':main()
