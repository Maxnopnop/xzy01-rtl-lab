"""Static public-original design and transfer package; never invokes model or EDA."""
import hashlib,importlib.util,json,re,sys,zipfile
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
RAG=HERE.parent/'fixed-input-rag-v2';BASE=HERE.parent/'fixed-input-direct-rtl-v1'
MODELS=['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def text(name,value):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value.encode())
def grams(s):
    t=re.findall(r'[a-z][a-z0-9_]*',s.lower());return {tuple(t[i:i+5]) for i in range(max(0,len(t)-4))}
def main():
    assert not (HERE/'slots.json').exists(),'Already prepared; no overwrite'
    inventory=read(HERE/'candidates-predeclared.json');selection=read(HERE/'selection.json')
    selected=[r for r in selection['rows'] if r['decision']=='SELECTED_CONDITIONAL']
    tree={r['path']:r for r in read(HERE/'metadata/tree.json')['tree'] if r['type']=='blob'}
    originals=[]
    for r in read(HERE/'access.json'):
        assert r['status']=='SAVED' and sha(HERE/r['path'])==r['sha256']
        if r['path'].startswith('upstream/'):
            path=r['path'].removeprefix('upstream/');raw=(HERE/r['path']).read_bytes()
            gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
            assert gitsha==tree[path]['sha'],path
            originals.append(dict(path=path,local=r['path'],sha256=r['sha256'],git_blob_sha1=gitsha,url=r['url'],retrieved_utc=r['utc']))
    write('original-data-manifest.json',dict(repository='https://github.com/NVlabs/verilog-eval',commit=inventory['commit'],
        license='MIT',copyright='2023-2024 NVIDIA Research Projects',files=originals,
        original_task_files=57,candidates=19,selected=2,individual_module_authorship='UNKNOWN'))
    with zipfile.ZipFile(HERE/'public-originals.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for item in originals:z.writestr(item['path'],(HERE/item['local']).read_bytes())
        z.writestr('PROVENANCE.json',(HERE/'original-data-manifest.json').read_bytes())
    with zipfile.ZipFile(HERE/'public-originals.zip') as z:
        for item in originals:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    # Lock old preparation artifacts, actual assets and original task sources; no old edits.
    prior={}
    for base in (BASE,RAG):
        for p in sorted(base.rglob('*')):
            if p.is_file():prior[p.relative_to(ROOT).as_posix()]=sha(p)
    write('previous-packets-bindings.json',prior)
    spec=importlib.util.spec_from_file_location('frozen_rag_retrieval',RAG/'retrieval_v2.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    chunks=read(RAG/'release/corpus/chunks.json');corpus=read(RAG/'release/corpus/manifest.json')
    corpus_bindings={}
    for path in ('retrieval_v2.py','release/corpus-lock.json','release/corpus/chunks.json','release/corpus/manifest.json','upstream/LICENSE','upstream/VerilogCodingStyle.md'):
        corpus_bindings[(RAG/path).relative_to(ROOT).as_posix()]=sha(RAG/path)
    write('rag-reuse-lock.json',corpus_bindings)
    # Historical exposure/near-duplicate evidence: no access to new model outputs exists.
    prior_files=read(BASE/'prior-bindings.json')
    hashes={}
    for name,h in prior_files.items():hashes.setdefault(h,[]).append(name)
    specs=[]
    for mf in ('tasks/manifest.json','benchmarks/dev10/tasks/manifest.json','benchmarks/paired-v1/manifest.json'):
        data=read(ROOT/mf);entries=data if isinstance(data,list) else data['tasks']
        specs.extend((mf+'#'+s['id'],s['spec']) for s in entries)
    history=[]
    for row in selection['rows']:
        value=(HERE/row['files']['prompt.txt']['path']).read_bytes().decode('utf-8')
        a=grams(value);matches=[]
        for name,old in specs:
            b=grams(old);j=len(a&b)/len(a|b) if a|b else 0.;matches.append((j,name))
        history.append(dict(id=row['id'],exact_prior_file_matches={k:hashes.get(v['sha256'],[])[:20] for k,v in row['files'].items()},
            closest_prior_specs=[{'jaccard':j,'path':n} for j,n in sorted(matches,reverse=True)[:3]],
            manual_decision=row['decision'],manual_reason=row['reason']))
    write('history-review.json',dict(scope='Prior22358-file byte hash inventory plus current custom/dev10/paired original spec manifests; exact matches capped20 displayed paths per asset',
        rows=history,limitations='No exact match is not proof of no exposure; functional near-duplicate judgments in selection take precedence over lexical scores. Public training contamination UNKNOWN.'))
    system=(BASE/'prompts/system.txt').read_bytes().decode('utf-8')
    text('project-wrapper/system.txt',system)
    records=[];contamination=[]
    for row in selected:
        task=row['id'];raw=(HERE/row['files']['prompt.txt']['path']).read_bytes();query=raw.decode('utf-8')
        assert query.encode()==raw
        retrieved=mod.retrieve(query,chunks)
        retrieved['selected_chunks']=[next(c for c in chunks if c['id']==i) for i in retrieved['selected_ids']]
        write(f'retrieval/{task}.json',retrieved)
        material='\n\n'.join(f'[{c["id"]}; {c["section"]}; lines {c["start_line"]}-{c["end_line"]}]\n{c["text"]}' for c in retrieved['selected_chunks'])
        context=('\n\n<generic_reference_context>\nThese are generic style excerpts, not new task requirements. '
            'The original specification above takes precedence.\nSource: lowRISC contributors; CC BY 4.0 '
            '(https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.\n'+corpus['source']['document_url']+'\n'+material+
            '\n</generic_reference_context>\n') if material else ''
        text(f'project-wrapper/{task}-rag-context.txt',context)
        for condition in ('no_rag','rag'):
            user=query+(context if condition=='rag' else '')
            text(f'prompts/{task}/{condition}/user.txt',user)
            text(f'prompts/{task}/{condition}/system.txt',system)
            messages=[dict(role='system',content=system),dict(role='user',content=user)]
            write(f'prompts/{task}/{condition}/messages.json',messages)
            for model in MODELS:write(f'requests/{task}/{condition}/{model}.json',dict(model=model,messages=messages,stream=False,max_completion_tokens=8192))
        cg=[(c['id'],grams(c['text'])) for c in chunks]
        # Compare both public prompt and answer/token syntax locally; neither enters corpus/query.
        artifacts=[(name,(HERE/item['path']).read_bytes().decode('utf-8')) for name,item in row['files'].items()]
        contamination.append(dict(task=task,corpus_task_name_hits=[c['id'] for c in chunks if task.lower() in c['text'].lower()],
            exact_paragraph_hits=[(c['id'],name) for c in chunks for name,value in artifacts if c['text'] in value],
            max_fivegram_jaccard=max((len(g&grams(v))/len(g|grams(v)) if g|grams(v) else 0) for _,g in cg for _,v in artifacts),
            manual_review='No task-specific mux256 or four-cycle reset-enable implementation in reused generic prose; no code/answers imported.',
            lexical_check_is_not_semantic_or_training_proof=True))
        records.append(dict(id=task,original_files=row['files'],reference_independence='NOT_ESTABLISHED_SAME_UPSTREAM',
            original_scoring='Verbatim upstream TB/ref, Mismatches report and process/timeout checks; no fixed private vectors added',
            rag_selected_ids=retrieved['selected_ids'],rag_context_sha256=sha(HERE/f'project-wrapper/{task}-rag-context.txt'),
            rag_added_bytes=len(context.encode()),original_prompt_sha256=hashlib.sha256(raw).hexdigest(),
            calibration_status='FAILED_COMPILE' if task.startswith('Prob018') else 'NOT_STARTED_STOPPED'))
    write('task-manifest.json',records);write('rag-contamination-review.json',contamination)
    slots=[]
    for sample in (1,2):
        for ti,row in enumerate(selected):
            rotation=(ti+sample-1)%3
            for mi,model in enumerate(MODELS[rotation:]+MODELS[:rotation]):
                conditions=('no_rag','rag') if (ti+mi+sample)%2==0 else ('rag','no_rag')
                for c in conditions:
                    task=row['id'];request=f'requests/{task}/{c}/{model}.json'
                    slots.append(dict(slot=len(slots)+1,task=task,model=model,condition=c,sample=sample,
                        pair_id=f'{task}/{model}/{sample}',request=request,request_sha256=sha(HERE/request),
                        messages_sha256=sha(HERE/f'prompts/{task}/{c}/messages.json'),state='PLANNED_NOT_STARTED',
                        original_test='PLANNED_BLOCKED',sat14='PLANNED_UNVALIDATED',sat32='PLANNED_UNVALIDATED',
                        reset_events='NOT_APPLICABLE_COMBINATIONAL' if task.startswith('Prob018') else 'PLANNED_UNVALIDATED'))
    write('slots.json',slots)
    write('target-accounting.json',dict(maximum_target_tasks=5,selected_tasks=2,unfilled_strata=['arithmetic','registers','counter'],
        maximum_proposed_slots=60,actual_proposed_slots=24,unfilled_target_slots=36,
        unfilled_are_not_model_failures=True,no_refill=True,old_60_slot_plan_superseded_not_additive=True))
    budget=read(RAG/'budget.json')
    budget.update(model_calls=24,calls_per_model=8,calls_per_condition=12,completion_cap_total=196608,
        completion_cap_per_model=65536,completion_cap_per_condition=98304,whole_batch_wall_seconds=10800,
        model_phase_wall_seconds=4800,yosys_calls_max=48,icarus_fixed_max=24,icarus_events_max=12,
        icarus_sat_witness_max=48,icarus_total_max=84,calibration_runs=0,
        preparation_calibration='Separate stopped run: 1 compile, 0 simulations; no retries',
        model_generation_authorized=False)
    write('budget.json',budget)
    write('fairness-matrix.json',[dict(model=m,condition=c,tasks=2,samples_per_task=2,calls=4,
       max_completion_tokens=8192,completion_cap=32768,timeout_seconds=180,concurrency=1,
       temperature=None,seed=None,reasoning_effort=None,common_parameter_support='UNVERIFIED',
       prompt_group='same task and condition; exactly shared across all models/samples',
       actual_tokens='UNKNOWN; RAG extra input separate, no equality claim') for m in MODELS for c in ('no_rag','rag')])
    write('service-review.json',dict(inherited=read(RAG/'service-review.json'),
        superseded_plan_sha256='a5ad53689820640e833845fde3366d1f6f9318d98db6efbbccd35b9acd73dff8',
        new_model_service_probes=0,changes_to_service=None,current_support='UNVERIFIED',
        hidden_wrapping_and_hard_cap_blockers_persist=True))
    write('tools.json',read(RAG/'tools.json'))
    print(json.dumps({'original_files':len(originals),'selected':len(selected),'slots':len(slots),'zip_sha256':sha(HERE/'public-originals.zip')}))
if __name__=='__main__':main()
