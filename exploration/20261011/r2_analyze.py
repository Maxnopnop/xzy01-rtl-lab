"""Read-only R2 audit and predeclared aggregates; artifacts outside frozen run."""
import sys,json,re
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import batch,rtl_lab as lab,r2
KEYS=['input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens']

def main():
    run=r2.RUN;plan=r2.verify(run);summary=batch.read(run/'summary.json');lock=batch.read(run/'evidence-lock.json')
    assert {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}==set(lock)
    for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,rel
    receipt_count=0;generation_count=0;unknown=[]
    for j,row in zip(plan['jobs'],summary['rows']):
        assert j['id']==row['id'];folder=run/'jobs'/j['id']
        if row['status']=='PENDING':assert not (folder/'started.json').exists();continue
        assert batch.read(folder/'started.json')['reserved_calls']==1
        g=batch.read(folder/'generation.json')
        if g['status']!='GENERATED':unknown.append(dict(id=j['id'],status=g['status']));continue
        generation_count+=1;assert lab.digest((folder/'response.txt').read_bytes())==g['response_sha256']
        assert (folder/'call/exact-prompt.txt').read_bytes()==j['prompt'].encode()
        request=batch.read(folder/'call/codex_request.json');assert request['prompt']==j['prompt'] and request['requested_model']==plan['model']
        assert request['adapter_sha256']==plan['source_hashes']['codex_network_adapter.py']
        events=[json.loads(line) for line in (folder/'call/codex.stdout.log').read_text(encoding='utf-8').splitlines() if line.strip()]
        completed=[e for e in events if e.get('type')=='turn.completed'];assert completed[-1]['usage']==g['usage']
        assert not any(e.get('type') in ('error','turn.failed') for e in events)
        itemtypes={e.get('item',{}).get('type') for e in events if e.get('type','').startswith('item.')};assert itemtypes<={'agent_message','reasoning'}
        judge=batch.read(folder/'judge.json')
        assert lab.digest((folder/'testbench.sv').read_bytes())==j['spec']['tb_sha256']
        for asset,h in j['spec']['assets'].items():assert lab.digest((folder/asset).read_bytes())==h
        for key,directory in [(None,folder),('ir_rtl',folder/'ir_rtl'),('spec_diagnostic',folder/'spec_diagnostic')]:
            result=judge if key is None else judge[key]
            if result['status'] not in ('PASS','FUNCTION_FAIL'):continue
            for stage in ('compile','simulate'):
                process=batch.read(directory/(stage+'.json'))
                assert process['returncode']==0 and not process['timeout'] and not process['output_limit']
            if key is not None:
                assert lab.digest((directory/'testbench.sv').read_bytes())==result['tb_sha256']
                assert lab.digest((directory/'agreement.hex').read_bytes())==result['vectors_sha256']
            receipt=(directory/'verdict.txt').read_text().strip()
            match=re.fullmatch(r'RTL_LAB_V1 ([0-9a-f]+) checks=(\d+) errors=(\d+)',receipt)
            assert match and match[1]==result['receipt_nonce']
            expected=j['spec']['checks'] if key is None else result['checks'];assert int(match[2])==expected
            assert (int(match[3])==0)==(result['status']=='PASS')
            receipt_count+=1
    arms={}
    for arm in ('regeneration','feedback'):
        rows=[r for r in summary['rows'] if r['arm']==arm];generated=[r for r in rows if r.get('generation',{}).get('status')=='GENERATED']
        usage={k:sum(r['usage'][k] for r in generated if isinstance((r.get('usage') or {}).get(k),(int,float))) if all(isinstance((r.get('usage') or {}).get(k),(int,float)) for r in generated) and generated else None for k in KEYS}
        passes=sum(r['status']=='PASS' for r in rows);out=usage['output_tokens']
        arms[arm]=dict(planned=len(rows),started=sum(r['status']!='PENDING' for r in rows),generated=len(generated),statuses=dict(Counter(r['status'] for r in rows)),usage=usage,
                       elapsed_seconds=sum(r.get('generation',{}).get('elapsed_seconds',0) for r in rows),generation_seconds=sum(r.get('generation',{}).get('generation_seconds',0) for r in rows),
                       pass_per_1000_output_tokens=passes*1000/out if out else None,cost='UNKNOWN; no billing information')
    comparisons=summary['comparisons'];strata={}
    for kind in ('REAL_RETAINED_IR','INJECTED_FAULT'):
        cs=[c for c in comparisons if c['kind']==kind];strata[kind]=dict(planned_pairs=len(cs),effects=dict(Counter(c['effect'] for c in cs)))
    matched=[c for c in comparisons if c['output_token_ratio_le2'] and c['effect']!='inconclusive']
    output=dict(status='PASS',checked_utc=lab.utc(),kind='PREDECLARED_R2_AGGREGATES_AND_ENGINEERING_AUDIT',plan_sha256=batch.read(run/'plan-lock.json')['sha256'],
                planned_slots=20,started=summary['started'],generated=generation_count,pending=summary['statuses'].get('PENDING',0),statuses=summary['statuses'],dispatch=batch.read(run/'dispatch.json'),
                verified_evidence_files=len(lock),verified_icarus_receipts=receipt_count,arms=arms,effects=dict(Counter(c['effect'] for c in comparisons)),family_clusters=summary['task_clusters'],strata=strata,
                descriptive_output_token_ratio_le2=dict(pairs=matched,count=len(matched),effects=dict(Counter(c['effect'] for c in matched)),note='Descriptive only; does not match total tokens, reasoning, compute or visible prompt text'),
                infrastructure_failures=unknown,yosys='NOT_RUN',limitations='Five families, two repeats, fixed initial IR. Not an end-to-end comparison, natural error rate or equal actual compute/cost claim. No post-hoc filtering of primary denominator.')
    batch.atomic(HERE/'r2-analysis.json',output);print(json.dumps({k:v for k,v in output.items() if k not in ('family_clusters','descriptive_output_token_ratio_le2')},indent=2))
if __name__=='__main__':main()
