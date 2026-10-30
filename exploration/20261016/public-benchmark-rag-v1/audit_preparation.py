"""Offline audit and historical byte checks; no compiler/model calls."""
import hashlib,importlib.util,json,re,sys,time,zipfile
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BASE=HERE.parent/'fixed-input-direct-rtl-v1';RAG=HERE.parent/'fixed-input-rag-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def check(base,lock):
    for path,h in read(lock).items():assert sha(base/path)==h,path
def main():
    check(ROOT,HERE/'previous-packets-bindings.json')
    check(ROOT,BASE/'prior-bindings.json')
    check(ROOT,HERE/'rag-reuse-lock.json')
    for base in (BASE,RAG):
        check(base,base/'packet-lock.json')
    check(HERE/'reference-calibration',HERE/'reference-calibration/evidence-lock.json')
    log=read(HERE/'access.json');assert len(log)==63 and len({r['url'] for r in log})==63
    for r in log:assert r['status']=='SAVED' and sha(HERE/r['path'])==r['sha256']
    data=read(HERE/'original-data-manifest.json');assert len(data['files'])==61
    tree={r['path']:r['sha'] for r in read(HERE/'metadata/tree.json')['tree'] if r['type']=='blob'}
    with zipfile.ZipFile(HERE/'public-originals.zip') as z:
        assert set(z.namelist())=={r['path'] for r in data['files']}|{'PROVENANCE.json'}
        for r in data['files']:
            original=(HERE/r['local']).read_bytes()
            assert hashlib.sha256(original).hexdigest()==r['sha256']
            assert z.read(r['path'])==original
            assert hashlib.sha1(b'blob '+str(len(original)).encode()+b'\x00'+original).hexdigest()==tree[r['path']]
    selection=read(HERE/'selection.json');assert selection['reviewed']==19 and selection['selected']==2
    selected=[r for r in selection['rows'] if r['decision']=='SELECTED_CONDITIONAL']
    assert [r['id'] for r in selected]==['Prob018_mux256to1','Prob095_review2015_fsmshift']
    inventory=read(HERE/'candidates-predeclared.json')
    assert [r['id'] for r in selection['rows']]==[r['id'] for r in inventory['candidates']]
    retriever=load('retriever',RAG/'retrieval_v2.py');chunks=read(RAG/'release/corpus/chunks.json')
    timing={};payloads=0
    for r in selected:
        task=r['id'];raw=(HERE/r['files']['prompt.txt']['path']).read_bytes();query=raw.decode('utf-8')
        start=time.perf_counter();expected=retriever.retrieve(query,chunks);timing[task]=time.perf_counter()-start
        saved=read(HERE/f'retrieval/{task}.json')
        assert all(saved[k]==v for k,v in expected.items())
        addition=(HERE/f'project-wrapper/{task}-rag-context.txt').read_bytes()
        for condition in ('no_rag','rag'):
            content=(HERE/f'prompts/{task}/{condition}/user.txt').read_bytes()
            assert content==raw+(addition if condition=='rag' else b'')
            messages=read(HERE/f'prompts/{task}/{condition}/messages.json')
            assert messages[1]['content'].encode()==content
            assert messages[0]['content'].encode()==(HERE/'project-wrapper/system.txt').read_bytes()
            equal=[]
            for model in ('gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol'):
                request=read(HERE/f'requests/{task}/{condition}/{model}.json')
                assert request['model']==model and request['messages']==messages
                assert request['max_completion_tokens']==8192
                del request['model'];equal.append(request);payloads+=1
            assert all(x==equal[0] for x in equal)
    slots=read(HERE/'slots.json');assert len(slots)==24
    assert set(Counter((s['task'],s['model'],s['condition']) for s in slots).values())=={2}
    for s in slots:
        assert s['state']=='PLANNED_NOT_STARTED' and sha(HERE/s['request'])==s['request_sha256']
    budget=read(HERE/'budget.json');assert budget['model_calls']==24 and budget['completion_cap_total']==24*8192
    assert sum(s['reset_events']=='NOT_APPLICABLE_COMBINATIONAL' for s in slots)==12
    parser=load('original_receipt',HERE/'original_receipt.py')
    cases=[((0,0,'Mismatches: 0 in 10 samples\n',False),'ORIGINAL_PASS'),
           ((0,0,'Mismatches: 1 in 10 samples\n',False),'ORIGINAL_FUNCTION_FAIL'),
           ((0,0,'Mismatches: 0 in 0 samples\n',False),'INVALID_ORIGINAL_RECEIPT'),
           ((0,0,'Mismatches: 0 in 10 samples\nMismatches: 0 in 10 samples\n',False),'INVALID_ORIGINAL_RECEIPT'),
           ((0,0,'Mismatches: 0 in 10 samples\nTIMEOUT\n',False),'TIMEOUT'),
           ((0,1,'Mismatches: 0 in 10 samples\n',False),'SIM_ERROR'),
           ((4294967295,None,'',False),'COMPILE_FAIL_UNCLASSIFIED')]
    for args,want in cases:assert parser.classify(*args)==want
    rows=read(HERE/'supplemental/Prob095_review2015_fsmshift/diagnostic-events.json')
    # Alternative edge-index arithmetic verifies proposed expectation rows, not hardware.
    edge_number=0;lastclk=0;last_reset_edge=None
    for row in rows:
        if row['clk'] and not lastclk:
            edge_number+=1
            if row['reset']:last_reset_edge=edge_number
        expected=None if last_reset_edge is None else int(edge_number-last_reset_edge<4)
        assert row['expected']==expected
        assert row['sample_time']==row['drive_time']+1
        lastclk=row['clk']
    assert len(rows)==31 and sum(r['score'] for r in rows)==29
    for task in [r['id'] for r in selected]:
        for bound in (14,32):
            script=(HERE/f'supplemental/{task}/check-{bound}.ys').read_text()
            assert f'-seq {bound} ' in script and 'set-init-zero' not in script and 'async2sync' not in script
            assert ('-set-at 1 reset 1' in script)==task.startswith('Prob095')
    calibration=read(HERE/'reference-calibration/results.json')
    assert len(calibration)==1 and len(calibration[0]['phases'])==1
    assert calibration[0]['phases'][0]['returncode']==4294967295
    assert not list((HERE/'reference-calibration').rglob('simulate.json'))
    out=dict(status='PASS_STATIC_PREPARATION_WITH_RETAINED_CALIBRATION_FAILURE',
        original_upstream_files=61,candidate_task_files=57,zip_members=62,screened=19,selected=2,planned_slots=24,
        full_proposed_payloads_checked=payloads,original_prompt_bytes_preserved=True,service_actual_prompt_equality='UNVERIFIED',
        prior_historical_files=len(read(BASE/'prior-bindings.json')),previous_preparation_files=len(read(HERE/'previous-packets-bindings.json')),
        byte_mismatches=0,receipt_parser_cases=len(cases),diagnostic_rows_checked=31,formal_templates_static_checked=4,
        retrieval_seconds=timing,timing_scope='local function replay only; not full preparation or model inference cost',
        actual_model_calls=0,actual_embedding_rerank_calls=0,actual_compiles=1,actual_simulations=0,actual_sat_calls=0,
        calibration_status='FAILED_STOPPED_NO_RETRY',reference_functional_validation='NOT_ESTABLISHED',
        execution_status='BLOCKED',audit_independence='same-author static check; coordinator review pending')
    (HERE/'offline-audit.json').write_bytes((json.dumps(out,indent=2)+'\n').encode())
    print(json.dumps(out))
if __name__=='__main__':main()
