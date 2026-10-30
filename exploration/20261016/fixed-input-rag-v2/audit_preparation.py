"""Offline contract checks. Never imports production runners or invokes tools/models."""
import hashlib,importlib.util,json,time,sys
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];BASE=HERE.parent/'fixed-input-direct-rtl-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_lock(base,lock):
    for n,h in read(lock).items():assert sha(base/n)==h,n
def main():
    check_lock(BASE,BASE/'packet-lock.json')
    assert set(read(BASE/'packet-lock.json'))=={p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file() and p.name!='packet-lock.json'}
    check_lock(ROOT,HERE/'baseline-bindings.json');check_lock(ROOT,HERE/'source-lock.json')
    check_lock(HERE,HERE/'corpus-lock.json');check_lock(HERE,HERE/'release/corpus-lock.json')
    for r in read(HERE/'access.json'):
        assert r['status']=='SAVED' and sha(HERE/r['path'])==r['sha256']
    assert len({r['url'] for r in read(HERE/'access.json')})==4
    selected=read(BASE/'task-manifest.json')
    originals={s['id']:s for s in read(ROOT/'benchmarks/paired-v1/manifest.json')['tasks']}
    spec=importlib.util.spec_from_file_location('retrieval_audit_only',HERE/'retrieval_v2.py')
    retrieval=importlib.util.module_from_spec(spec);spec.loader.exec_module(retrieval)
    chunks,excluded=retrieval.build_corpus()
    assert chunks==read(HERE/'release/corpus/chunks.json')
    assert excluded==read(HERE/'release/corpus/exclusions.json')
    assert len(chunks)==18 and not any('][' in c['text'] or '```' in c['text'] for c in chunks)
    text=(HERE/'upstream/VerilogCodingStyle.md').read_text(encoding='utf-8').splitlines()
    for c in chunks:
        assert '\n'.join(text[c['start_line']-1:c['end_line']])==c['text']
        assert hashlib.sha256(c['text'].encode()).hexdigest()==c['sha256']
    elapsed={};prompt_checks=0;assets=0
    for s in selected:
        task=s['id'];original=originals[task]['spec']
        for asset in s['source_assets']+s['r1c_assets']+[s['procedural_reference']]:
            assert sha(ROOT/asset['path'])==asset['sha256']==sha(BASE/asset['frozen_copy']);assets+=1
        assert (BASE/f'prompts/{task}/user.txt').read_bytes()==original.encode()
        before=time.perf_counter();recomputed=retrieval.retrieve(original,chunks)
        elapsed[task]=time.perf_counter()-before
        saved=read(HERE/f'release/retrieval/{task}.json')
        assert all(saved[k]==v for k,v in recomputed.items())
        assert saved['selected_chunks']==[next(c for c in chunks if c['id']==i) for i in saved['selected_ids']]
        addition=(HERE/f'prompts/{task}/rag-context.txt').read_text(encoding='utf-8')
        for c in saved['selected_chunks']:assert c['text'] in addition
        for condition in ('no_rag','rag'):
            messages=read(HERE/f'prompts/{task}/{condition}/messages.json')
            assert messages[0]['content']==(BASE/'prompts/system.txt').read_text(encoding='utf-8')
            assert messages[1]['content']==original+(addition if condition=='rag' else '')
            bodies=[]
            for model in ('gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol'):
                payload=read(HERE/f'requests/{task}/{condition}/{model}.json')
                assert payload['model']==model and payload['messages']==messages
                assert payload['max_completion_tokens']==8192 and payload['stream'] is False
                del payload['model'];bodies.append(json.dumps(payload,ensure_ascii=False,sort_keys=True))
                prompt_checks+=1
            assert len(set(bodies))==1
        for row in s['r1b_scripts']:
            old=(ROOT/row['original']['path']).read_text(encoding='utf-8')
            new=(BASE/row['planned']).read_text(encoding='utf-8')
            assert new==old.replace('read_verilog -sv miter.sv\n','read_verilog -sv reference.sv dut.sv miter.sv\n',1)
        old_folder=(ROOT/s['procedural_reference']['path']).parent
        old=(old_folder/'miter.sv').read_text(encoding='utf-8')
        top=old[old.rindex('\nmodule miter('):]
        assert (BASE/f'tasks/{task}/r1b/miter.sv').read_text(encoding='utf-8')==top.replace('gate A(',s['module']+' A(')
    assert retrieval.retrieve('zxqnonexistenttoken',chunks)['no_hit']
    ties=[dict(id='B',section='generic',text='clock reset'),dict(id='A',section='generic',text='clock reset')]
    assert retrieval.retrieve('clock',ties)['selected_ids']==['A','B']
    slots=read(HERE/'slots.json');assert len(slots)==60
    counts=Counter((s['task'],s['model'],s['condition']) for s in slots)
    assert len(counts)==30 and set(counts.values())=={2}
    assert set(s['state'] for s in slots)=={'PLANNED_NOT_STARTED'}
    for s in slots:
        assert sha(HERE/s['request'])==s['request_sha256']
        assert sha(HERE/f'prompts/{s["task"]}/{s["condition"]}/messages.json')==s['messages_sha256']
    b=read(HERE/'budget.json')
    assert b['model_calls']==60 and b['completion_cap_total']==60*8192
    assert b['yosys_calls_max']==120 and b['icarus_total_max']==240
    prior=read(HERE/'prior-verification.json');assert prior['status']=='PASS' and prior['checked_files']==22358
    assert prior['baseline_sha256']==sha(BASE/'prior-bindings.json')
    contamination=read(HERE/'contamination-audit.json')
    assert not any(x['exact_text_in_comparison'] or x['task_name_marker'] for x in contamination['chunks'])
    result=dict(status='PASS_OFFLINE_PREPARATION_ONLY',prompt_payloads_checked=prompt_checks,
        planned_slots=60,original_asset_byte_bindings=assets,source_bindings=len(read(HERE/'source-lock.json')),
        retrieval_replays=5,no_hit_and_tie_checks='PASS',corpus_release_chunks=18,
        local_retrieval_replay_seconds=elapsed,local_retrieval_total_seconds=sum(elapsed.values()),
        retrieval_timing_scope='in-process replay only, excludes download/build/startup; not model latency',
        r1b_static_wrapper_and_script_checks=15,historical_preservation=prior,
        model_calls=0,eda_calls=0,execution_readiness='BLOCKED',
        limitations='Same-author static audit, not coordinator independence, service observation, runtime adapter or EDA validation')
    (HERE/'offline-audit.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k not in ('historical_preservation','local_retrieval_replay_seconds')}))
if __name__=='__main__':main()
