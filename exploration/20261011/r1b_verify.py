"""R1b-only verification; never rewrite R1 frozen verification/results."""
import sys,json,re,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import batch,rtl_lab as lab,paired_bank as bank,mutation_study as ms,r1b_v2 as impl

def main():
    parser_tests=[]
    def check(label,result,expected):
        baseline=dict(stdout='',stderr='',timeout=False,output_limit=False,returncode=0);baseline.update(result);observed=impl.classify(baseline);assert observed==expected,(label,observed);parser_tests.append(dict(label=label,observed=observed,kind='SYNTHETIC_PARSER_TEST'))
    check('timeout',dict(timeout=True),'TIMEOUT');check('output_limit',dict(output_limit=True),'OUTPUT_LIMIT')
    check('unsupported',dict(returncode=1,stderr='ERROR: Failed to import cell ABC'),'UNSUPPORTED')
    check('syntax',dict(returncode=1,stderr='ERROR: syntax error'),'SYNTAX_ERROR')
    check('other_tool_error',dict(returncode=1,stderr='ERROR: arbitrary'),'TOOL_ERROR')
    check('ambiguous_exit0',dict(stdout='Nothing conclusive'),'UNPARSED_TOOL_RESULT')
    check('no_model',dict(stdout='SAT proof finished - no model found: SUCCESS!'),'NO_COUNTEREXAMPLE_WITHIN_BOUND')
    check('counterexample',dict(stdout='SAT proof finished - model found: FAIL!'),'COUNTEREXAMPLE_FOUND')
    spec=next(s for s in ms.development_specs() if s['id']=='event_parity')
    with tempfile.TemporaryDirectory(dir=HERE,prefix='r1b-env-test-') as tmp:
        with patch.object(lab,'run_process',side_effect=OSError('Synthetic missing executable')):
            result=impl.sat(Path(tmp)/'case','event_parity',impl.reference('event_parity',spec['module'],spec['ports']),spec,14)
        assert result['status']=='ENV_ERROR';parser_tests.append(dict(label='missing_executable',observed='ENV_ERROR',kind='MOCK_ERROR_ADAPTER_TEST'))
    locks=[]
    for name in ('compound-v1','delayed-v1','factorial20-v1','formal-v1','r1b-v1','r1b-v2'):
        run=HERE/'runs'/name;lock=batch.read(run/'evidence-lock.json')
        files={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'};assert files==set(lock),name
        for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(name,rel)
        plan=batch.read(run/'plan.json')
        for rel,h in plan['source_hashes'].items():assert lab.digest((ROOT/rel).read_bytes())==h,(name,rel)
        locks.append(dict(run=name,files=len(lock),source_files=len(plan['source_hashes']),plan_sha256=lab.digest((run/'plan.json').read_bytes())))
    run=HERE/'runs/r1b-v2';rows=batch.read(run/'history-results.json');selection=batch.read(run/'selection.json')
    assert selection==batch.read(HERE/'runs/r1b-v1/selection.json')
    assert len(rows)==len(selection['rows'])==24
    bound_stats=Counter();witness_stats=Counter();v1_copy_same=0;duplicates=Counter();details=[]
    v1rows=batch.read(HERE/'runs/r1b-v1/history-results.json')
    for row,item,old in zip(rows,selection['rows'],v1rows):
        assert row['source']==item;index=row['selection_index'];source=(ROOT/item['dut_path']).read_bytes();assert lab.digest(source)==item['rtl_sha256']
        assert lab.digest((ROOT/item['result_path']).read_bytes())==item['result_sha256'];duplicates[item['rtl_sha256']]+=1
        for result in row['results']:
            folder=HERE/result['directory'];assert (folder/'original.sv').read_bytes()==source
            assert result['original_sha256']==item['rtl_sha256']
            spec=next(s for s in ms.development_specs() if s['id']==item['task'])
            mapped,n=re.subn(rb'\bmodule\s+'+spec['module'].encode()+rb'\b',b'module gate',source,count=1);assert n==1 and (folder/'mapped.sv').read_bytes()==mapped
            assert lab.digest(mapped)==result['mapped_sha256'];bound_stats[result['status']]+=1
            if 'witness' in result:
                witness=result['witness'];witness_stats[witness['status']]+=1
                assert (folder/'witness/dut.sv').read_bytes()==source
                assert lab.digest((folder/'witness/testbench.sv').read_bytes())==witness['tb_sha256']
                receipt=(folder/'witness/verdict.txt').read_text().strip();assert receipt.startswith('RTL_LAB_V1 '+witness['receipt_nonce']+' ')
                assert witness['status']=='FUNCTION_FAIL'
        oldfolder=HERE/old['results'][0]['directory'];v1_copy_same+=int((oldfolder/'original.sv').read_bytes()==source)
        assert [r['status'] for r in row['results']]==[r['status'] for r in old['results']]
        first=row['results'][0]
        details.append(dict(index=index,task=item['task'],model=item['model'],original_status=item['original_status'],bits=''.join(str(b) for rst,b in first.get('witness',{}).get('inputs',[]) if rst) or None,expected=first.get('witness',{}).get('expected_post'),statuses=[r['status'] for r in row['results']]))
    # Preserve source snapshots without modifying old snapshot directories.
    for rel,h in batch.read(run/'plan.json')['source_hashes'].items():
        dest=HERE/'snapshots/r1b-v2'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes((ROOT/rel).read_bytes())
        assert lab.digest(dest.read_bytes())==h
    output=dict(status='PASS',checked_utc=lab.utc(),locks=locks,old_four_files=sum(r['files'] for r in locks[:4]),selection_matches_v1=True,historical_samples=24,source_bindings=48,status_counts=dict(bound_stats),witness_counts=dict(witness_stats),v1_actual_copy_matches=v1_copy_same,distinct_selected_rtl=len(duplicates),duplicate_clusters=[dict(sha256=h,count=n) for h,n in duplicates.items() if n>1],parser_adapter_tests=parser_tests,details=details,limits='Synthetic parser/adapter tests are separate from real Yosys/Icarus evidence; no actual timeout or unsupported historical sample occurred.')
    batch.atomic(HERE/'r1b-verification.json',output);print(json.dumps({k:v for k,v in output.items() if k not in ('details','locks','parser_adapter_tests','duplicate_clusters')},indent=2))
if __name__=='__main__':main()
