"""Offline development-only mutation coverage and diagnostic calibration."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import backends
import batch
import fsm_checks
import fsm_ir
import paired_bank as bank
import paired_study as study
import rtl_lab as lab


def development_specs():
    manifest = bank.load()
    names = manifest['split']['development']
    return [s for s in manifest['tasks'] if s['id'] in names]


def mutations(reference):
    """All single edits in five declared operator classes, never sampled."""
    original = reference['data']; names = [s['name'] for s in original['states']]
    for index, edge in enumerate(original['transitions']):
        for destination in names:
            if destination == edge['to']: continue
            obj = copy.deepcopy(original); obj['transitions'][index]['to'] = destination
            yield f'edge_{index:02d}_{destination}', 'transition', obj
    for index, state in enumerate(original['states']):
        obj = copy.deepcopy(original); obj['states'][index]['output'] ^= 1
        yield 'output_'+state['name'], 'state_output', obj
    for field, value in [('kind', 'sync' if original['reset']['kind']=='async' else 'async'),
                         ('active', 1-original['reset']['active'])]:
        obj=copy.deepcopy(original); obj['reset'][field]=value
        yield 'reset_'+field, 'reset_'+field, obj
    for state in names:
        if state == original['reset']['state']: continue
        obj=copy.deepcopy(original); obj['reset']['state']=state
        yield 'reset_state_'+state, 'reset_state', obj


def raw(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def check_public(contracts, task, candidate):
    """Use only the supplied public profile; never consult private references."""
    if task not in contracts: raise ValueError('Task not in supplied public profile')
    return bank.feedback(candidate, contracts[task]['contract'])


def strengthen(spec, cases):
    """Greedy covering of observed dev blind spots; no minimality claim."""
    contract=copy.deepcopy(spec['public_contract'])
    missed=[r for r in cases if r['is_fault'] and r['public_before']=='PUBLIC_CHECK_PASS']
    candidates={r['diagnosis']['shortest_counterexample']['bits'] for r in missed}
    if '' in candidates: raise ValueError('Reset-output mismatch escaped public reset check')
    additions=[]
    while missed:
        alternatives=[]
        for bits in sorted(candidates, key=lambda b:(len(b),b)):
            expected=[r[3] for r in bank.oracle(spec['id'],[(0,0)]+[(1,int(b)) for b in bits])][1:]
            # Independent procedural oracle, not copied from the mutated graph.
            if expected != fsm_ir.trace(bank.graph(spec['id']),bits): raise ValueError('Oracle disagreement')
            hit=[r['id'] for r in missed if fsm_ir.trace(fsm_ir.parse(raw(r['ir'])),bits)!=expected]
            alternatives.append((len(hit),bits,expected,hit))
        count,bits,outputs,hit=min(alternatives,key=lambda x:(-x[0],len(x[1]),x[1]))
        if not count: raise ValueError('Cannot cover a dev blind spot')
        contract['examples'].append(dict(bits=bits,outputs=outputs))
        additions.append(dict(bits=bits,outputs=outputs,newly_detected=hit))
        missed=[r for r in missed if r['id'] not in hit]; candidates.remove(bits)
    return dict(contract=contract,additions=additions,
        provenance='Development-tuned using exact counterexamples from this declared mutation set; not held-out evidence.')


def analyze():
    cases=[]; contracts={}; summaries=[]
    for spec in development_specs():
        reference=bank.graph(spec['id']); selected=[]
        for ident,kind,obj in mutations(reference):
            diagnosis=fsm_ir.product_check(fsm_ir.parse(raw(obj)),reference)
            selected.append(dict(id=spec['id']+'__'+ident,task=spec['id'],operator=kind,ir=obj,
                diagnosis=diagnosis,is_fault=diagnosis['status']=='IR_SPEC_MISMATCH',
                public_before=bank.feedback(raw(obj),spec['public_contract'])['status']))
        strengthened=strengthen(spec,selected); contracts[spec['id']]=strengthened
        for row in selected:
            row['public_after']=bank.feedback(raw(row['ir']),strengthened['contract'])['status']
            if row['is_fault'] != (row['public_after']=='PUBLIC_CHECK_FAIL'): raise ValueError('Strengthened check mismatch')
        if bank.feedback(raw(reference['data']),strengthened['contract'])['status']!='PUBLIC_CHECK_PASS':
            raise ValueError('Reference rejected')
        summaries.append(dict(task=spec['id'],mutations=len(selected),faults=sum(r['is_fault'] for r in selected),
            equivalent=sum(not r['is_fault'] for r in selected),
            public_misses_before=sum(r['is_fault'] and r['public_before']=='PUBLIC_CHECK_PASS' for r in selected),
            public_misses_after=sum(r['is_fault'] and r['public_after']=='PUBLIC_CHECK_PASS' for r in selected),
            added_examples=[a['bits'] for a in strengthened['additions']]))
        cases.extend(selected)
    return dict(cases=cases,contracts=contracts,coverage=summaries)


def fixed_sim(folder,spec,rtl,tools,args):
    folder.mkdir(parents=True); lab.write_text(folder/'dut.sv',rtl)
    for name in ('testbench.sv',*spec['assets']):
        (folder/name).write_bytes((bank.ROOT/spec['id']/name).read_bytes())
    result=backends.IcarusBackend().evaluate(folder,spec,tools,args)
    return dict(result,rtl_sha256=lab.digest((folder/'dut.sv').read_bytes()),tb_sha256=spec['tb_sha256'])


def agreement_sim(folder,spec,ir,rtl,inputs,tools,args):
    folder.mkdir(parents=True);lab.write_text(folder/'dut.sv',rtl)
    binding=fsm_checks.write_agreement_test(folder,spec,ir,inputs,spec['ports'])
    return dict(binding,**backends.IcarusBackend().evaluate(folder,binding,tools,args),
                mismatches=fsm_checks.mismatch_log(folder))


def execute(run):
    if run.exists(): raise ValueError('Choose a new run directory; prior evidence is immutable')
    data=analyze();run.mkdir(parents=True)
    source_names=(*batch.CODE_FILES,'fsm_ir.py','fsm_checks.py','paired_bank.py','paired_study.py','fsm_study.py','mutation_study.py')
    plan=dict(schema=1,kind='OFFLINE_SINGLE_EDIT_MUTATION_CALIBRATION',new_model_calls=0,
        operators=['transition','state_output','reset_kind','reset_active','reset_state'],
        source_hashes={n:lab.digest((batch.ROOT/n).read_bytes()) for n in source_names},
        bank_lock_sha256=lab.digest((bank.ROOT/'bank-lock.json').read_bytes()),
        tasks=[s['id'] for s in development_specs()],mutations=len(data['cases']),
        note='All DUTs are deterministic fixtures; not model generations. Public strengthening is fitted to development faults.')
    for name,obj in [('plan.json',plan),('cases.json',data['cases']),('contracts-v2.json',data['contracts'])]:batch.atomic(run/name,obj)
    batch.atomic(run/'input-lock.json',{n:lab.digest((run/n).read_bytes()) for n in ('plan.json','cases.json','contracts-v2.json')})
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10)
    tools=lab.inspect_tools(args,run);batch.atomic(run/'environment.json',tools)
    results=[];matrix=[];references=[]
    for spec in development_specs():
        task=spec['id'];reference=bank.graph(task);inputs=batch.read(bank.ROOT/task/'inputs.json')
        if fsm_ir.timed_vectors(reference,inputs)!=bank.oracle(task,inputs): raise ValueError('Oracle disagreement')
        ref_rtl=bank.fixture_rtl(reference,spec['ports'],spec['module'])
        baseline=fixed_sim(run/'references'/task,spec,ref_rtl,tools,args)
        if baseline['status']!='PASS': raise ValueError('Reference failed')
        references.append(dict(task=task,**baseline))
        selected=[r for r in data['cases'] if r['task']==task]
        for case in selected:
            candidate=fsm_ir.parse(raw(case['ir']));rtl=bank.fixture_rtl(candidate,spec['ports'],spec['module'])
            root=run/'mutants'/case['id']
            observed=fixed_sim(root/'spec',spec,rtl,tools,args)
            agrees=agreement_sim(root/'agreement',spec,candidate,rtl,inputs,tools,args)
            if observed['status'] not in ('PASS','FUNCTION_FAIL') or agrees['status']!='PASS':
                raise ValueError('Fixture/toolchain inconsistency: '+case['id'])
            if not case['is_fault'] and observed['status']!='PASS': raise ValueError('Equivalent mutation falsely rejected')
            row=dict(id=case['id'],is_fault=case['is_fault'],spec_test=observed,ir_agreement=agrees,
                fixed_test_miss=case['is_fault'] and observed['status']=='PASS')
            if row['fixed_test_miss']:
                ce=case['diagnosis']['shortest_counterexample']
                if ce is None: raise ValueError('Reset metadata blind spot needs a timed witness')
                witness=[(0,0)]+[(1,int(b)) for b in ce['bits']]
                row['new_witness_test']=agreement_sim(root/'witness',spec,reference,rtl,witness,tools,args)
                if row['new_witness_test']['status']!='FUNCTION_FAIL': raise ValueError('Counterexample not reproduced')
            results.append(row)
        wrong=[r for r in selected if r['is_fault'] and r['operator']=='state_output']
        first=wrong[0];second=wrong[1]
        # Two distinct output flips are independently known semantic faults.
        ir1=fsm_ir.parse(raw(first['ir']));ir2=fsm_ir.parse(raw(second['ir']))
        conditions=[('correct_ir_correct_rtl',reference,reference,'ALL_PASS'),
                    ('wrong_ir_faithful_rtl',ir1,ir1,'SPEC_TO_IR_ERROR'),
                    ('correct_ir_wrong_rtl',reference,ir1,'IR_TO_RTL_ERROR'),
                    ('wrong_ir_correct_rtl',ir1,reference,'RTL_CORRECTS_IR_ON_TESTS'),
                    ('wrong_ir_different_wrong_rtl',ir1,ir2,'BOTH_DIVERGE')]
        for name,ir,implementation,expected in conditions:
            folder=run/'matrix'/(task+'__'+name);folder.mkdir(parents=True)
            rtl=bank.fixture_rtl(implementation,spec['ports'],spec['module'])
            row=study.judge(folder,spec,rtl,raw(ir['data']),tools,args)
            if row['localization']!=expected:raise ValueError('Localization calibration failed: '+task+'/'+name)
            matrix.append(dict(task=task,condition=name,expected=expected,ir=ir['data'],result=row))
        print(task+': '+json.dumps(next(c for c in data['coverage'] if c['task']==task)),flush=True)
    summary=dict(schema=1,kind=plan['kind'],new_model_calls=0,coverage=data['coverage'],
        fixed_test_misses=sum(r['fixed_test_miss'] for r in results),
        statuses=dict(Counter(r['spec_test']['status'] for r in results)),
        references=references,results=results,localization_matrix=matrix,
        calibration_passes=len(matrix),calibration_planned=5*len(references),
        limits=['Single-edit faults only, hand-authored development tasks, no natural-error prevalence estimate.',
                'New public examples are selected against this mutation set, so coverage is an in-sample engineering metric.',
                'Diagnostic fixture accuracy is not accuracy on unseen model-generated circuits.'])
    batch.atomic(run/'summary.json',summary)
    return summary


def curate(run,dest):
    if dest.exists():raise ValueError('Evidence destination already exists')
    summary=batch.read(run/'summary.json');dest.mkdir(parents=True)
    for name in ('plan.json','input-lock.json','cases.json','contracts-v2.json','environment.json','summary.json'):
        (dest/name).write_bytes((run/name).read_bytes())
    for part in ('references','mutants','matrix'):
        for path in (run/part).rglob('dut.sv'):
            target=dest/path.relative_to(run);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    batch.atomic(dest/'evidence-lock.json',{p.relative_to(dest).as_posix():lab.digest(p.read_bytes()) for p in dest.rglob('*') if p.is_file()})
    return summary


def verify(folder):
    folder=Path(folder); lock=batch.read(folder/'evidence-lock.json')
    inventory={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
    if inventory!=set(lock):raise ValueError('Evidence inventory changed')
    for name,expected in lock.items():
        path=(folder/name).resolve()
        if not path.is_relative_to(folder.resolve()) or lab.digest(path.read_bytes())!=expected:
            raise ValueError('Evidence changed: '+name)
    plan=batch.read(folder/'plan.json')
    for name,expected in plan['source_hashes'].items():
        if lab.digest((batch.ROOT/name).read_bytes())!=expected:raise ValueError('Frozen source changed: '+name)
    if lab.digest((bank.ROOT/'bank-lock.json').read_bytes())!=plan['bank_lock_sha256']:raise ValueError('Bank changed')
    for name,expected in batch.read(folder/'input-lock.json').items():
        if lab.digest((folder/name).read_bytes())!=expected:raise ValueError('Frozen inputs changed')
    analysis=analyze();summary=batch.read(folder/'summary.json')
    if analysis['cases']!=batch.read(folder/'cases.json') or analysis['contracts']!=batch.read(folder/'contracts-v2.json'):
        raise ValueError('Enumeration or public contracts do not reproduce')
    if analysis['coverage']!=summary['coverage']:raise ValueError('Coverage summary mismatch')
    rows=summary['results']
    if len(rows)!=len(analysis['cases']) or {r['id'] for r in rows}!={r['id'] for r in analysis['cases']}:
        raise ValueError('Missing or duplicate mutation result')
    for row in rows:
        root=folder/'mutants'/row['id']; dut=(root/'spec/dut.sv').read_bytes()
        if lab.digest(dut)!=row['spec_test']['rtl_sha256'] or dut!=(root/'agreement/dut.sv').read_bytes():
            raise ValueError('Mutant DUT binding mismatch')
        if row['ir_agreement']['status']!='PASS':raise ValueError('Fixture disagrees with its IR')
    if dict(Counter(r['spec_test']['status'] for r in rows))!=summary['statuses']:raise ValueError('Status count mismatch')
    matrix=summary['localization_matrix']
    if len(matrix)!=5*len(plan['tasks']) or len({(r['task'],r['condition']) for r in matrix})!=len(matrix):
        raise ValueError('Missing or duplicate matrix cell')
    for row in matrix:
        root=folder/'matrix'/(row['task']+'__'+row['condition'])
        if row['expected']!=row['result']['localization'] or lab.digest((root/'dut.sv').read_bytes())!=row['result']['rtl_sha256']:
            raise ValueError('Matrix result/DUT mismatch')
    return dict(status='PASS',files=len(lock),mutations=len(rows),matrix_cells=len(matrix),new_model_calls=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('analyze')
    run=sub.add_parser('run');run.add_argument('--run-dir',required=True)
    cur=sub.add_parser('curate');cur.add_argument('--run-dir',required=True);cur.add_argument('--destination',required=True)
    checker=sub.add_parser('check');checker.add_argument('--contracts',required=True);checker.add_argument('--task',required=True);checker.add_argument('--ir',required=True)
    ver=sub.add_parser('verify');ver.add_argument('--evidence',required=True)
    args=parser.parse_args()
    try:
        if args.command=='analyze': print(json.dumps(analyze()['coverage'],indent=2))
        elif args.command=='run':execute(Path(args.run_dir).resolve())
        elif args.command=='curate':curate(Path(args.run_dir).resolve(),Path(args.destination).resolve())
        elif args.command=='verify':print(json.dumps(verify(Path(args.evidence).resolve()),indent=2))
        else:
            result=check_public(batch.read(Path(args.contracts)),args.task,Path(args.ir).read_text(encoding='utf-8'))
            print(json.dumps(result,indent=2));return int(result['status']!='PUBLIC_CHECK_PASS')
    except (OSError,ValueError,KeyError,lab.LabError) as exc:parser.exit(1,'ERROR: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
