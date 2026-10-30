"""Freeze proposed requests and finite design, not a generation/EDA runner."""
import hashlib,json,re,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BASE=HERE.parent/'fixed-input-direct-rtl-v1'
MODELS=['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol']
TASKS=['rt_sequence','sticky_alarm','event_parity','request_delay','debounce3']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,obj):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def text(name,value):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value.encode())
def grams(value):
    toks=re.findall(r'[a-z][a-z0-9_]*',value.lower())
    return {tuple(toks[i:i+5]) for i in range(max(0,len(toks)-4))}
def main():
    assert not (HERE/'slots.json').exists(),'Do not regenerate design'
    manifest=read(BASE/'task-manifest.json');corpus=read(HERE/'release/corpus/manifest.json')
    context_notes=[]
    for task in TASKS:
        system=(BASE/'prompts/system.txt').read_text(encoding='utf-8')
        original=(BASE/f'prompts/{task}/user.txt').read_text(encoding='utf-8')
        retrieved=read(HERE/f'release/retrieval/{task}.json')
        header=('\n\n<generic_reference_context>\n'
            'The following are retrieved generic style-guide excerpts, not task requirements or solutions. '
            'The original specification above takes precedence. Do not infer extra task behavior from these excerpts.\n'
            'Source: lowRISC contributors, lowRISC Verilog Coding Style Guide, CC BY 4.0 '
            '(https://creativecommons.org/licenses/by/4.0/). Excerpts selected without text rewriting.\n'
            'Pinned source: '+corpus['source']['document_url']+'\n')
        body='\n\n'.join(f'[{c["id"]}; {c["section"]}; lines {c["start_line"]}-{c["end_line"]}]\n{c["text"]}'
                          for c in retrieved['selected_chunks'])
        addition=header+body+'\n</generic_reference_context>\n' if body else ''
        text(f'prompts/{task}/rag-context.txt',addition)
        for condition in ('no_rag','rag'):
            user=original+(addition if condition=='rag' else '')
            messages=[{'role':'system','content':system},{'role':'user','content':user}]
            text(f'prompts/{task}/{condition}/system.txt',system)
            text(f'prompts/{task}/{condition}/user.txt',user)
            write(f'prompts/{task}/{condition}/messages.json',messages)
            for model in MODELS:
                write(f'requests/{task}/{condition}/{model}.json',dict(model=model,messages=messages,
                    stream=False,max_completion_tokens=8192))
        context_notes.append(dict(task=task,selected_ids=retrieved['selected_ids'],no_hit=retrieved['no_hit'],
            added_utf8_bytes=len(addition.encode()),added_characters=len(addition),
            context_sha256=sha(HERE/f'prompts/{task}/rag-context.txt'),actual_token_count=None))
    write('context-summary.json',context_notes)
    slots=[]
    for sample in (1,2):
        for ti,task in enumerate(TASKS):
            rotation=(ti+sample-1)%3
            for mi,model in enumerate(MODELS[rotation:]+MODELS[:rotation]):
                conditions=('no_rag','rag') if (ti+sample+mi)%2==0 else ('rag','no_rag')
                for condition in conditions:
                    req=f'requests/{task}/{condition}/{model}.json'
                    slots.append(dict(slot=len(slots)+1,task=task,condition=condition,model=model,sample=sample,
                        pair_id=f'{task}/{model}/{sample}',request=req,request_sha256=sha(HERE/req),
                        messages_sha256=sha(HERE/f'prompts/{task}/{condition}/messages.json'),
                        state='PLANNED_NOT_STARTED',attempt_cap=1,
                        checks=['original_fixed','R1b_14','R1b_32','R1c_original_events']))
    write('slots.json',slots)
    write('task-manifest.json',dict(tasks=manifest,asset_root=BASE.relative_to(ROOT).as_posix(),
        original_manifest_sha256=sha(BASE/'task-manifest.json'),
        input_versions='Exactly the baseline pinned original bytes; no RAG data enters checkers',
        supported_families=5,task_ambiguity='request_delay wording is flagged; no selective clarification added'))
    budget=read(BASE/'budget.json')
    budget.update(model_calls=60,calls_per_model=20,calls_per_condition=30,samples_per_task_model_condition=2,
        completion_cap_total=491520,completion_cap_per_model=163840,completion_cap_per_condition=245760,
        whole_batch_wall_seconds=28800,model_phase_wall_seconds=12000,yosys_calls_max=120,
        icarus_fixed_max=60,icarus_events_max=60,icarus_sat_witness_max=120,icarus_total_max=240,
        disk_bytes_max=1073741824,baseline_30_is_superseded_not_additive=True,
        actual_input_tokens='UNKNOWN before authorized execution; RAG bytes/characters recorded separately',
        embedding_calls=0,rerank_calls=0,training_runs=0,retrieval_top_k=3)
    write('budget.json',budget)
    write('fairness-matrix.json',[dict(model=m,condition=c,task_count=5,samples_per_task=2,
        calls=10,max_completion_tokens_each=8192,completion_cap=81920,concurrency=1,
        timeout_seconds=180,temperature=None,seed=None,reasoning_effort=None,
        unspecified_parameter_note='Omitted consistently, but provider common defaults/support unverified; blocker.',
        shared_prompt_group='task+condition; all model/sample prompt bytes identical',
        retrieval='one frozen deterministic result per task, reused' if c=='rag' else 'none',
        actual_tokens_and_cost='report actual input/output/reasoning/cache separately, missing is UNKNOWN')
        for m in MODELS for c in ('no_rag','rag')])
    # Lexical contamination triage: all retained historical DUTs in evidence plus original specs.
    candidates=[]
    for s in read(ROOT/'benchmarks/paired-v1/manifest.json')['tasks']:
        candidates.append((f'paired-v1/spec/{s["id"]}',s['spec']))
    historical=[];seen=set()
    for name,h in read(BASE/'prior-bindings.json').items():
        if name.startswith('evidence/') and name.endswith('/dut.sv'):
            historical.append(name)
            if h not in seen:
                seen.add(h);candidates.append((name,(ROOT/name).read_text(encoding='utf-8-sig')))
    bags=[(name,grams(value)) for name,value in candidates]
    chunks=read(HERE/'release/corpus/chunks.json');triage=[]
    for chunk in chunks:
        cg=grams(chunk['text']);near=[]
        for name,bag in bags:
            overlap=len(cg&bag);score=overlap/len(cg|bag) if cg|bag else 0
            near.append((score,overlap,name))
        score,overlap,name=max(near)
        triage.append(dict(chunk_id=chunk['id'],closest=name,fivegram_jaccard=score,shared_grams=overlap,
            exact_text_in_comparison=any(chunk['text'] in value for _,value in candidates),
            task_name_marker=any(t in chunk['text'].lower() for t in TASKS+['1001','sequence_detector'])))
    write('contamination-audit.json',dict(method='ASCII lowercase word five-gram Jaccard; exact paragraph and task-marker checks; manual prose review',
        scope='All paired-v1 spec strings and all historical evidence/**/dut.sv, deduplicated by original byte SHA',
        historical_dut_paths=len(historical),unique_dut_hashes=len(seen),comparisons=len(candidates),chunks=triage,
        manual_review='No selected chunk contains task logic, complete module, candidate IR, model answer or private vector. Generic language/style only.',
        limitations='Lexical checks cannot prove semantic non-duplication or training absence; corpus selected with development-task knowledge. '
                    'Prior OpenTitan work references the same lowRISC ecosystem; no unseen/heldout claim.',
        training_contamination='UNKNOWN',model_output_driven_selection=False))
    bindings={}
    for p in sorted(BASE.rglob('*')):
        if p.is_file():bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    write('baseline-bindings.json',bindings)
    write('source-lock.json',read(BASE/'source-lock.json'))
    write('tools.json',read(BASE/'tools.json'))
    write('service-review.json',read(BASE/'service-review.json'))
    write('preparation-receipt.json',dict(status='PREPARED_BLOCKED',models=3,conditions=2,tasks=5,samples=2,
        planned_slots=60,baseline_30_superseded=True,model_calls=0,actual_sent_prompts=0,
        embedding_calls=0,rerank_calls=0,training_calls=0,eda_compiles=0,eda_simulations=0,sat_calls=0,
        corpus_sources=1,release_chunks=len(chunks),public_source_http_requests=4,
        retries=0,service_probes=0,actual_full_prompt_equality='UNVERIFIED; proposed serialized content equal within task+condition',
        executable_dispatcher=None,execution_authorized=False))
    print(json.dumps({'slots':len(slots),'chunks':len(chunks),'historical_dut_paths':len(historical),'status':'PREPARED_BLOCKED'}))
if __name__=='__main__':main()
