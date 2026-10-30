"""R5 completed-run audit, outside frozen sources. No model/RTL replay."""
import sys,json,re
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;BASE=P/'r5';ROOT=P.parents[1];sys.path[:0]=[str(BASE),str(ROOT)]
import runner,tasks,intent,prompts,batch,rtl_lab as lab
RUN=runner.RUN
def check_seal(run):
    lock=batch.read(run/'evidence-lock.json');actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')};assert set(lock)==actual
    for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(run,rel)
    return len(lock)
def check_sim(folder,task,rows,status,raw):
    if status in ('EXTRACTION_ERROR','RTL_REJECTED'):
        try:lab.extract_rtl(raw,tasks.TASKS[task]['module'])
        except lab.LabError as e:assert e.status==status;return None
        raise AssertionError('Unreproduced policy status')
    assert (folder/'dut.sv').read_bytes()==lab.extract_rtl(raw,tasks.TASKS[task]['module']).encode()
    spec=tasks.TASKS[task];iw=sum(w for n,w in spec['inputs']);ow=sum(w for n,w in spec['outputs'])
    words=[f'{(((r["clk"]*2+r["rst_n"])<<iw)|r["input"])<<ow|r["expected"]:x}' for r in rows]
    assert (folder/'vectors.hex').read_bytes()==('\n'.join(words)+'\n').encode()
    comp=batch.read(folder/'compile.json')
    if status=='COMPILE_FAIL':assert comp['returncode']!=0;assert not (folder/'simulate.json').exists();return dict(folder=str(folder.relative_to(BASE)),compile_fail=True)
    assert comp['returncode']==0
    sim=batch.read(folder/'simulate.json');assert sim['returncode']==0 and not sim['timeout'] and not sim['output_limit']
    nonce=next(x.split('=',1)[1] for x in sim['command'] if x.startswith('+nonce='));m=re.fullmatch(r'RTL_LAB_V1 (\w+) checks=(\d+) errors=(\d+)',(folder/'verdict.txt').read_text().strip());assert m and m[1]==nonce and int(m[2])==len(rows)
    assert (int(m[3])==0)==(status=='PASS'),(folder,status,m[3])
    return dict(folder=str(folder.relative_to(BASE)),nonce=nonce,checks=int(m[2]),errors=int(m[3]),status=status)
def main():
    p=runner.verify();sealed=check_seal(RUN);rows=batch.read(RUN/'results.json');summary=batch.read(RUN/'summary.json');dispatch=batch.read(RUN/'dispatch.json');cli=[];checks=[];ir_cache={}
    def contract(jid,task):
        key=(jid,task)
        if key not in ir_cache:
            f=RUN/'jobs'/jid/'generation.json';g=batch.read(f) if f.exists() else None
            ir_cache[key]=intent.check(runner.raw(RUN,jid),'structured',task,batch.read(runner.ASSETS/f'{task}-private.json')) if g and g['status']=='GENERATED' else (dict(status=g['status'] if g else 'PENDING',stage='generation'),None)
        return ir_cache[key]
    for j,r in zip(p['jobs'],rows):
        assert {k:v for k,v in j.items() if k!='prompt'}=={k:r[k] for k in j if k!='prompt'}
        folder=RUN/'jobs'/j['id'];g=r.get('generation')
        if not g:assert r['status']=='PENDING';continue
        assert g==batch.read(folder/'generation.json')
        if g['status']=='UNKNOWN_INTERRUPTED':assert (folder/'started.json').exists();continue
        if 'prompt' in j:expected=j['prompt']
        elif j['role']=='first_rtl':expected=prompts.first(j['task'],'structured',runner.raw(RUN,j['intent_id']))
        elif j['role']=='direct_second':expected=prompts.second(j['task'],runner.raw(RUN,j['first_id']))
        else:
            fb=batch.read(RUN/'jobs'/j['first_id']/'public-feedback.json');expected=prompts.branch(j['task'],j['representation'],None,runner.raw(RUN,j['first_id']),fb if j['arm']=='feedback' else None)
        call=folder/'call'
        if g['status']=='INPUT_LIMIT':assert (folder/'exact-prompt.txt').read_bytes()==expected.encode();assert not (folder/'started.json').exists();continue
        assert (call/'exact-prompt.txt').read_bytes()==expected.encode()
        if g['status']!='GENERATED':continue
        raw=runner.raw(RUN,j['id']);req=batch.read(call/'codex_request.json');cp=batch.read(call/'codex.json')
        assert cp['returncode']==0 and not cp['timeout'] and not cp['output_limit'] and cp['command'][-1]=='-'
        assert req['prompt']==expected and req['prompt_bytes']==g['prompt_bytes']==len(expected.encode()) and req['prompt_sha256']==g['prompt_sha256']==lab.digest(expected.encode())
        assert (call/'codex_prompt.txt').read_bytes()==expected.encode();assert req['requested_model']==p['model'] and req['reasoning_effort']==p['reasoning'] and req['prompt_transport']=='stdin_utf8_file'
        for label in ('codex_version','codex_auth'):assert batch.read(call/(label+'.json'))['returncode']==0
        events=[json.loads(x) for x in (call/'codex.stdout.log').read_text().splitlines() if x.strip()];completed=[e for e in events if e.get('type')=='turn.completed'];assert len(completed)==1 and completed[0].get('usage')==g['usage']
        assert not any(e.get('type') in ('error','turn.failed') for e in events)
        it={e.get('item',{}).get('type') for e in events if e.get('type','').startswith('item.')};assert it<={'agent_message','reasoning'} and g['tools_used'] is False
        final=(call/'model_output.raw.txt').read_bytes();assert final.decode().replace('\r\n','\n').replace('\r','\n')==raw
        thread=next(e['thread_id'] for e in events if e.get('type')=='thread.started');assert thread==g['codex_thread_id']
        cli.append(dict(id=j['id'],thread_id=thread,version=(call/'codex_version.stdout.log').read_text().strip(),exe_sha256=req['codex_executable_sha256'],prompt_bytes=g['prompt_bytes'],prompt_sha256=g['prompt_sha256'],response_sha256=g['response_sha256'],raw_final_sha256=lab.digest(final),events_sha256=lab.digest((call/'codex.stdout.log').read_bytes()),usage=g['usage'],generation_seconds=cp['elapsed_seconds'],elapsed_seconds=g['elapsed_seconds'],item_types=sorted(it)))
        judged=r['judge'];private=batch.read(runner.ASSETS/f'{j["task"]}-private.json')
        if j['role']=='intent':assert judged['intent_spec']==contract(j['id'],j['task'])[0]
        else:
            c=check_sim(folder/'hidden-spec',j['task'],private,judged['rtl_spec']['status'],raw)
            if c:checks.append(c)
            if j['representation']=='structured':
                ir,values=contract(j['intent_id'],j['task']);assert judged['intent_spec']==ir
                if values is None:assert judged['rtl_intent']['status']=='NOT_ASSESSABLE'
                else:
                    c=check_sim(folder/'hidden-intent',j['task'],[dict(e,expected=v) for e,v in zip(private,values)],judged['rtl_intent']['status'],raw)
                    if c:checks.append(c)
            if (folder/'public-feedback.json').exists():
                fb=batch.read(folder/'public-feedback.json');assert set(fb)<={'status','mismatches','scope','message'}
                c=check_sim(folder/'public',j['task'],batch.read(runner.ASSETS/f'{j["task"]}-public.json'),fb['status'],raw)
                if c:checks.append(c)
    assert len({r['thread_id'] for r in cli})==len(cli)
    assert runner.summarize(rows,p)==summary
    # Preparation packet is a retained pre-execution subset; new run files are intentional additions.
    prep=batch.read(BASE/'packet-lock.json')
    for rel,h in prep.items():assert lab.digest((BASE/rel).read_bytes())==h,rel
    prior=batch.read(BASE.parent/'r4/prior-bindings.json')
    for rel,h in prior.items():assert lab.digest((ROOT/rel).read_bytes())==h,rel
    oldfiles=sum(check_seal(d) for d in (BASE.parent/'r4/runs').iterdir() if d.is_dir() and (d/'evidence-lock.json').exists())
    ledger={}
    usage_keys=('input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens')
    def known_usage(group):
        completed=[r for r in group if (r.get('generation') or {}).get('status')=='GENERATED']
        return {k:sum(r['generation']['usage'][k] for r in completed) if completed and all(isinstance((r['generation'].get('usage') or {}).get(k),(int,float)) for r in completed) else None for k in usage_keys}
    for rep in ('structured','direct'):
        shared=[r for r in rows if r['representation']==rep and r['arm']=='shared'];reserved_shared=sum(bool((r.get('generation') or {}).get('model_called')) for r in shared)
        for arm in ('regeneration','feedback'):
            branches=[r for r in rows if r['representation']==rep and r['arm']==arm];reserved_branch=sum(bool((r.get('generation') or {}).get('model_called')) for r in branches)
            su=known_usage(shared);bu=known_usage(branches)
            ledger[rep+'_'+arm]=dict(planned_opportunities=18,planned_half_shared_calls=12,reserved_full=reserved_shared+reserved_branch,reserved_half=reserved_shared/2+reserved_branch,known_shared_usage=su,known_branch_usage=bu,known_half_shared_usage={k:su[k]/2+bu[k] if su[k] is not None and bu[k] is not None else None for k in usage_keys},unreported_reserved=sum((r.get('generation') or {}).get('status')=='UNKNOWN_INTERRUPTED' for r in shared+branches),**summary['strategies'][rep+'_'+arm])
    by_family={t:{rep:{role:dict(Counter(r['status'] for r in rows if r['task']==t and r['representation']==rep and (r['role']==role if role not in ('feedback','regeneration') else r['arm']==role))) for role in ('intent','first_rtl','direct_first','direct_second','regeneration','feedback')} for rep in ('structured','direct')} for t in tasks.TASKS}
    # Predeclared complete cost sensitivity, no threshold filtering.
    sensitivity={k:dict(main_denominator=v['denominator'],supported_ir_cases=sum(contract(c['id']+'__structured__intent',c['task'])[0]['status'] in ('PASS','FUNCTION_FAIL') for c in p['cases']) if k.startswith('structured') else None,allocated_input_per_pass=v['shared_half_usage']['input_tokens']/v['passes'] if v['passes'] and v['shared_half_usage']['input_tokens'] is not None else None,allocated_output_per_pass=v['shared_half_usage']['output_tokens']/v['passes'] if v['passes'] and v['shared_half_usage']['output_tokens'] is not None else None) for k,v in summary['strategies'].items()}
    result=dict(status='PASS',dispatch=dispatch,plan_sha256=batch.read(RUN/'plan-lock.json')['sha256'],sealed_files=sealed,sources=len(p['source_hashes']),preserved_preparation_files=len(prep),preserved_prior_bindings=len(prior),preserved_r4_sealed_files=oldfiles,actual_unique_cli_turns=len(cli),reserved_slots=summary['started'],pending=summary['statuses'].get('PENDING',0),known_completed_usage=known_usage(rows),unknown_reserved_usage='UNKNOWN; aggregate all-provider usage cannot be completed',compile_calls=len(list(RUN.rglob('compile.json'))),simulate_calls=len(list(RUN.rglob('simulate.json'))),event_checks=sum(c.get('checks',0) for c in checks),generation_seconds=sum(c['generation_seconds'] for c in cli),adapter_elapsed_seconds=sum(c['elapsed_seconds'] for c in cli),versions=dict(Counter(c['version'] for c in cli)),exe_hashes=dict(Counter(c['exe_sha256'] for c in cli)),prompt_byte_range=[min(c['prompt_bytes'] for c in cli),max(c['prompt_bytes'] for c in cli)] if cli else [],cost='UNKNOWN',summary=summary,by_family=by_family,ledger=ledger,sensitivity=sensitivity,cli=cli,judge_receipts=checks,scope='No model/simulator replay; binary bounded same-author references; raw evidence only')
    batch.atomic(BASE/'actual-analysis.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('summary','by_family','ledger','sensitivity','cli','judge_receipts')},indent=2))
if __name__=='__main__':main()
