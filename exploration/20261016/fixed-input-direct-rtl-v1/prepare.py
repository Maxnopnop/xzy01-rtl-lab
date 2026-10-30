"""Offline preparation only: no target-module imports, transport, or EDA execution."""
import ast
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'exploration/20261011'
BANK = ROOT / 'benchmarks/paired-v1'
TASKS = ['rt_sequence', 'sticky_alarm', 'event_parity', 'request_delay', 'debounce3']
MODELS = ['gpt-5.6-luna', 'gpt-5.6-terra', 'gpt-5.6-sol']

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(name, value):
    p = HERE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def text(name, value):
    p = HERE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(value.encode('utf-8'))

def main():
    assert not (HERE / 'packet-lock.json').exists(), 'Frozen packet; do not regenerate'
    assert not (HERE / 'task-manifest.json').exists(), 'Preparation outputs already exist'
    prior_path = HERE/'prior-bindings.json'
    if prior_path.exists():
        prior = read(prior_path)  # Preserve the first attempt's baseline, never re-baseline.
    else:
        prior = {}
        for base in (ROOT/'evidence', OLD, ROOT/'exploration/20261015'):
            for p in sorted(base.rglob('*')):
                if p.is_file():
                    prior[p.relative_to(ROOT).as_posix()] = sha(p)
        write('prior-bindings.json', prior)
    sources = {}
    def bind(p):
        rel = p.relative_to(ROOT).as_posix()
        sources[rel] = sha(p)
        return {'path': rel, 'sha256': sources[rel]}
    def copy(src, name):
        b = bind(src)
        dest = HERE / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        assert sha(dest) == b['sha256']
        return dict(b, frozen_copy=name)
    # Validate original bank lock, including unselected assets; never rebuild bank.
    bank_lock = read(BANK/'bank-lock.json')
    for rel, expected in bank_lock.items():
        assert sha(BANK/rel) == expected, rel
        bind(BANK/rel)
    bind(BANK/'bank-lock.json')
    manifest = read(BANK/'manifest.json')
    specs = {s['id']: s for s in manifest['tasks']}
    parsed = ast.parse((ROOT/'rtl_lab.py').read_text(encoding='utf-8-sig'))
    system = next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'SYSTEM_PROMPT' for t in n.targets))
    text('prompts/system.txt', system)
    for rel in ('AGENTS.md','FYP_FIXED_INPUT_RTL_RULES.md','README.md','ARCHITECTURE.md',
                'validation/R1BC_RULE_REVIEW_20261016.md','MODEL_ROUTE_RECOVERY.md',
                'rtl_lab.py','api_worker.py','codex_adapter.py','codex_network_adapter.py',
                'backends.py','batch.py','paired_bank.py','mutation_study.py','fsm_ir.py','fsm_checks.py'):
        bind(ROOT/rel)
    for rel in ('r1b_v2.py','timed_reset.py','R1B_PROTOCOL.md','R1B_AMENDMENT.md','R1C_PROTOCOL.md',
                'R1B_RESULTS.md','R1C_RESULTS.md','r1b-verification.json','r1c-verification.json'):
        bind(OLD/rel)
    r1b = OLD/'runs/r1b-v2'
    r1c = OLD/'runs/timed-reset-v1'
    for run in (r1b,r1c):
        lock = read(run/'evidence-lock.json')
        for rel, expected in lock.items():
            assert sha(run/rel) == expected, str(run/rel)
        for rel, expected in read(run/'plan.json')['source_hashes'].items():
            assert sha(ROOT/rel) == expected, rel
            bind(ROOT/rel)
        for name in ('plan.json','evidence-lock.json','environment.json','history-results.json'):
            bind(run/name)
    profiles = read(r1c/'events.json')
    bind(r1c/'events.json')
    history_b, history_c = read(r1b/'history-results.json'), read(r1c/'history-results.json')
    tasks = []
    for task in TASKS:
        spec = specs[task]
        assert spec['split'] == 'development'
        out = 'tasks/'+task+'/'
        assets = []
        for p in sorted((BANK/task).iterdir()):
            if p.is_file():
                assets.append(copy(p, out+'original/'+p.name))
        assert sha(BANK/task/'testbench.sv') == spec['tb_sha256']
        for name, expected in spec['assets'].items():
            assert sha(BANK/task/name) == expected
        # Exact decoded spec string, no strip, examples, feedback, IR, or clarification added.
        text('prompts/'+task+'/user.txt', spec['spec'])
        messages = [{'role':'system','content':system},{'role':'user','content':spec['spec']}]
        write('prompts/'+task+'/messages.json', messages)
        for model in MODELS:
            write('requests/'+task+'/'+model+'.json', {'model':model, 'messages':messages,
                  'stream':False,'max_completion_tokens':8192})
        cb = next(r for r in history_b if r['source']['task']==task)
        old14 = OLD/cb['results'][0]['directory']
        # Bind original procedural gold, keep original bytes and separate DUT unchanged.
        ref = copy(old14/'reference.sv', out+'r1b/reference.sv')
        old_miter = (old14/'miter.sv').read_text(encoding='utf-8')
        top = old_miter[old_miter.rindex('\nmodule miter('):]
        assert top.count('gate A(') == 1
        wrapper = top.replace('gate A(', spec['module']+' A(')
        text(out+'r1b/miter.sv', wrapper)
        bind(old14/'miter.sv')
        scripts = []
        for bound in (14,32):
            rr = next(r for r in cb['results'] if r['bound']==bound)
            old_script = OLD/rr['directory']/'check.ys'
            original = old_script.read_text(encoding='utf-8')
            assert original.startswith('read_verilog -sv miter.sv\n')
            derived = original.replace('read_verilog -sv miter.sv\n',
                                      'read_verilog -sv reference.sv dut.sv miter.sv\n',1)
            text(out+f'r1b/check-{bound}.ys', derived)
            scripts.append(dict(bound=bound, original=bind(old_script),
                                planned=out+f'r1b/check-{bound}.ys'))
        cc = next(r for r in history_c if r['source']['task']==task)
        old_c = r1c/'history'/f'{cc["selection_index"]:02d}_{task}'
        c_assets = [copy(old_c/name,out+'r1c/'+name) for name in ('events.bin','testbench.sv')]
        expected_bin = ''.join(f'{e["clk"]}{e["reset"]}{e["bit"]}{e["expected"]}\n' for e in profiles[task]).encode()
        assert (old_c/'events.bin').read_bytes().splitlines() == expected_bin.splitlines()
        assert sha(old_c/'events.bin') == cc['result']['events_sha256']
        assert sha(old_c/'testbench.sv') == cc['result']['tb_sha256']
        ambiguity = ('Terminology: accepting edge output 0, following cycle wording can be read ambiguously. '
                     'Frozen reference uses phase 0->1->2(q=1)->3. Do not clarify prompt or change expectations. '
                     'Keep this family in denominator; flag specification ambiguity in any timing-error claim.'
                     if task=='request_delay' else
                     'No additional ambiguity identified by static review; not proof of unique implementation.')
        tasks.append(dict(id=task,module=spec['module'],family=spec['family'],
             version='paired-v1 frozen development bank; rt_sequence retains dev10 clarification',
             original_spec_pointer=f'benchmarks/paired-v1/manifest.json#/tasks/{manifest["tasks"].index(spec)}/spec',
             source_assets=assets, original_checks=spec['checks'], ports=spec['ports'],
             input_to_model=['prompts/system.txt','prompts/'+task+'/user.txt'],
             prompt_sha256=sha(HERE/'prompts'/task/'messages.json'),
             procedural_reference=ref,r1b_scripts=scripts,r1c_assets=c_assets,
             r1c_event_count=len(profiles[task]),r1c_categories=dict(Counter(e['category'] for e in profiles[task])),
             ambiguity=ambiguity,heldout=False,source_origin=spec.get('origin',{'kind':'project-authored developer task'}),
             adaptation_status='STATIC_BOUND_NOT_RUNTIME_VALIDATED',execution_status='BLOCKED_SERVICE_AND_TRANSPORT'))
    write('task-manifest.json',tasks)
    slots=[]
    # Counterbalance deterministic order without putting model/sample/order into prompts.
    for sample in (1,2):
        for ti,task in enumerate(TASKS):
            rotation=(ti+sample-1)%3
            for model in MODELS[rotation:]+MODELS[:rotation]:
                slots.append(dict(slot=len(slots)+1,task=task,model=model,sample=sample,
                    request=f'requests/{task}/{model}.json',
                    request_sha256=sha(HERE/f'requests/{task}/{model}.json'),
                    state='PLANNED_NOT_STARTED',attempt_cap=1,
                    checks=['original_fixed','R1b_14','R1b_32','R1c_original_events']))
    write('slots.json',slots)
    write('budget.json',dict(proposal_only=True,model_calls=30,calls_per_model=10,samples_per_task_model=2,
        max_completion_tokens_per_call=8192,completion_cap_total=245760,
        completion_cap_per_model=81920,concurrency=1,request_timeout_seconds=180,
        whole_batch_wall_seconds=14400,model_phase_wall_seconds=6000,output_text_limit_bytes=131072,
        response_http_limit_bytes=1048576,formal_bounds=[14,32],yosys_calls_max=60,yosys_timeout_seconds=30,
        icarus_fixed_max=30,icarus_events_max=30,icarus_sat_witness_max=60,
        icarus_total_max=120,compile_timeout_seconds=15,simulation_timeout_seconds=10,
        disk_bytes_max=536870912,automatic_retry=0,replacement_samples=0,calibration_runs=0,
        monetary_charge='UNKNOWN; no purchase/topup authorized; requires verified account/endpoint before release',
        generation_stop='First auth/403/unsupported model/unknown outcome/transport or wrapper violation stops all new calls; no retry. '
                        'A complete but invalid RTL consumes its slot and is retained; no quality-based stopping.',
        verification_stop='Hash drift immediately stops all work; 3 consecutive infrastructure errors stop verification; pending retained',
        output_cap_semantics='Required common service-enforced combined completion budget incl reasoning if applicable; not yet verified'))
    tools = {'python':{'path':sys.executable,'sha256':sha(Path(sys.executable)),'version':sys.version},
             'icarus':{},'yosys':{'recorded_version':(r1b/'version.stdout.log').read_text().strip(),
                'version_source':bind(r1b/'version.stdout.log'),'current_installation_verified':False}}
    archived_env = read(r1b/'environment.json')
    for k,v in archived_env.items():
        p=Path(v['path'])
        tools['icarus'][k]=dict(v,current_sha256=sha(p) if p.is_file() else None,
                              current_matches_recorded=p.is_file() and sha(p)==v['sha256'],
                              version_observation='archived; binary hash checked now, not simulator execution')
    write('tools.json',tools)
    cfg=ROOT/'config.local.models.csv'
    with cfg.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    # No endpoint/key/env secret values are read out or copied to preparation packet.
    safe=[{'enabled':r.get('enabled'),'model':r.get('model')} for r in rows]
    write('service-review.json',dict(review_kind='LOCAL_STATIC_ONLY_NO_ENDPOINT_PROBE',
        local_csv_rows=safe,requested_models=MODELS,verified_supported_models=[],
        cli='Historical success is insufficient: hidden context not captured and max_output_tokens=None.',
        api='api_worker serializes supplied payload without local message additions. No verified real enabled requested-model route.',
        blocker='No evidence for server-side prompt wrapping, model support or enforced common output cap.',
        transport_selected=None,model_substitution=False,default_proxy_regression='Historical failure retained; no rerun or environment override'))
    write('source-lock.json',sources)
    write('preparation-receipt.json',dict(status='PREPARED_BLOCKED_NOT_EXECUTABLE',model_calls=0,
        service_probes=0,eda_compiles=0,eda_simulations=0,sat_calls=0,calibration_runs=0,
        task_families=5,models=3,planned_slots=30,actual_sent_prompts=0,
        actual_prompt_equality='NOT_OBSERVED; frozen proposed request equality only',
        old_evidence_files_bound=len(prior),source_files_bound=len(sources)))
    print(json.dumps({'tasks':len(tasks),'slots':len(slots),'prior':len(prior),'sources':len(sources),
                      'status':'PREPARED_BLOCKED_NOT_EXECUTABLE'}))

if __name__=='__main__':
    main()
