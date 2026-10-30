"""Development-only exhaustive three-locus mutation probe; zero model calls."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
from collections import Counter
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / 'outputs' / 'rtl-batch'
sys.path.insert(0, str(REPO))
import mutation_study as old
import paired_bank as bank
import fsm_ir
import rtl_lab as lab


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def differences(a, b, path=()):
    if isinstance(a, dict):
        return [x for key in a for x in differences(a[key], b[key], path + (key,))]
    if isinstance(a, list):
        return [x for i in range(len(a)) for x in differences(a[i], b[i], path + (i,))]
    return [] if a == b else [(path, b)]


def set_value(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def enumerate_pairs(reference):
    singles = []
    for name, kind, obj in old.mutations(reference):
        diff = differences(reference['data'], obj)
        assert len(diff) == 1
        singles.append((name, kind, diff[0]))
    seen = set()
    for a, b, c in itertools.combinations(singles, 3):
        if len({a[2][0], b[2][0], c[2][0]}) != 3:
            continue  # Two alternatives to the same field are not two edits.
        obj = copy.deepcopy(reference['data'])
        for change in (a[2], b[2], c[2]):
            set_value(obj, *change)
        assert len(differences(reference['data'], obj)) == 3
        encoded = old.raw(obj)
        assert encoded not in seen
        seen.add(encoded)
        yield a[0] + '__' + b[0] + '__' + c[0], '+'.join(sorted((a[1], b[1], c[1]))), obj


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--simulate', action='store_true')
    args = p.parse_args()
    out = Path(args.out).resolve()
    if out.exists():
        raise ValueError('Use a fresh evidence directory')
    out.mkdir(parents=True)
    specs = old.development_specs()
    profile_path = REPO / 'evidence/mutation-v1/contracts-v2.json'
    profiles = json.loads(profile_path.read_text(encoding='utf-8'))
    source_names = ['mutation_study.py', 'paired_bank.py', 'fsm_ir.py', 'fsm_checks.py',
                    'rtl_lab.py', 'backends.py', 'batch.py']
    plan = dict(kind='OFFLINE_THREE_DISTINCT_LOCUS_MUTATIONS', new_model_calls=0,
                tasks=[s['id'] for s in specs], operators='All unordered compatible triples of existing single edits',
                source_hashes={n: sha(REPO/n) for n in source_names}, probe_sha256=sha(Path(__file__)),
                profile_sha256=sha(profile_path), bank_lock_sha256=sha(bank.ROOT/'bank-lock.json'),
                simulate_selection='All v2 public-pass non-equivalent mutants; plus one correct reference per development family',
                max_rtl_cases=250, scope='Development-only; no held-out graphs, no profile refitting, no model or commercial EDA calls')
    write(out/'plan.json', plan)
    rows = []
    coverage = []
    for spec in specs:
        task = spec['id']
        reference = bank.graph(task)
        selected = []
        assert bank.feedback(old.raw(reference['data']), profiles[task]['contract'])['status'] == 'PUBLIC_CHECK_PASS'
        for ident, kind, obj in enumerate_pairs(reference):
            candidate = fsm_ir.parse(old.raw(obj))
            diagnosis = fsm_ir.product_check(candidate, reference)
            fault = diagnosis['status'] == 'IR_SPEC_MISMATCH'
            before = bank.feedback(old.raw(obj), spec['public_contract'])['status']
            after = bank.feedback(old.raw(obj), profiles[task]['contract'])['status']
            ce = diagnosis['shortest_counterexample']
            if ce is not None:
                bits = ce['bits']
                expected = [r[3] for r in bank.oracle(task, [(0, 0)] + [(1, int(b)) for b in bits])][1:]
                assert expected == fsm_ir.trace(reference, bits)
                if bits:
                    assert fsm_ir.trace(candidate, bits) != expected
            row = dict(id=task+'__'+ident, task=task, operator=kind, ir=obj, is_fault=fault,
                       diagnosis=diagnosis, public_v1=before, public_v2=after)
            selected.append(row)
        faults = [r for r in selected if r['is_fault']]
        lengths = Counter(str(len(r['diagnosis']['shortest_counterexample']['bits']))
                          for r in faults if r['diagnosis']['shortest_counterexample'] is not None)
        sweep = []
        for depth in range(1, 11):
            # A single complete depth-L trace collection also checks its prefixes.
            # Reset output and reset metadata remain mandatory public checks.
            detected = sum(bool(r['diagnosis']['reset_contract_errors']) or
                           (r['diagnosis']['shortest_counterexample'] is not None and
                            len(r['diagnosis']['shortest_counterexample']['bits']) <= depth) for r in faults)
            sweep.append(dict(depth=depth, traces=2**depth, input_cycles=depth*2**depth,
                              detected=detected, faults=len(faults)))
        item = dict(task=task, pairs=len(selected), faults=len(faults), equivalent=len(selected)-len(faults),
                    v1_missed=sum(r['public_v1']=='PUBLIC_CHECK_PASS' for r in faults),
                    v2_missed=sum(r['public_v2']=='PUBLIC_CHECK_PASS' for r in faults),
                    shortest_witness_lengths=dict(lengths), exhaustive_trace_sweep=sweep,
                    v1_examples=len(spec['public_contract']['examples']),
                    v2_examples=len(profiles[task]['contract']['examples']),
                    v1_cycles=sum(len(e['bits']) for e in spec['public_contract']['examples']),
                    v2_cycles=sum(len(e['bits']) for e in profiles[task]['contract']['examples']))
        coverage.append(item)
        rows.extend(selected)
        print(json.dumps(item, ensure_ascii=False), flush=True)
    write(out/'cases.json', rows)
    blind = [r for r in rows if r['is_fault'] and r['public_v2']=='PUBLIC_CHECK_PASS']
    write(out/'blindspots.json', blind)
    summary = dict(kind=plan['kind'], new_model_calls=0, coverage=coverage,
                   total_pairs=len(rows), faults=sum(r['is_fault'] for r in rows),
                   equivalent=sum(not r['is_fault'] for r in rows), v2_blindspots=len(blind),
                   rtl_results=[], limits=['Mutation population is not natural LLM error prevalence.',
                   'v2 was fitted on single edits in these same development families; three-edit evidence is not a held-out benchmark.',
                   'Exact graph equivalence is not arbitrary RTL equivalence.',
                   'Depth sweep is analytically inferred from exact shortest witnesses, not independent execution of every trace.'])
    write(out/'summary.json', summary)
    if args.simulate:
        if len(blind)+len(specs) > plan['max_rtl_cases']:
            raise ValueError('RTL case cap exceeded; analysis saved, choose a separate predeclared plan')
        tools_args = SimpleNamespace(iverilog=None, vvp=None, compile_timeout=15, sim_timeout=10)
        tools = lab.inspect_tools(tools_args, out)
        write(out/'environment.json', tools)
        results = []
        for spec in specs:
            task = spec['id']
            reference = bank.graph(task)
            fixtures = [(task+'__reference', reference, False)]
            fixtures += [(r['id'], fsm_ir.parse(old.raw(r['ir'])), True) for r in blind if r['task']==task]
            inputs = json.loads((bank.ROOT/task/'inputs.json').read_text(encoding='utf-8'))
            assert fsm_ir.timed_vectors(reference, inputs) == bank.oracle(task, inputs)
            for ident, candidate, is_fault in fixtures:
                rtl = bank.fixture_rtl(candidate, spec['ports'], spec['module'])
                folder = out/'rtl'/ident
                observed = old.fixed_sim(folder/'spec', spec, rtl, tools, tools_args)
                agrees = old.agreement_sim(folder/'agreement', spec, candidate, rtl, inputs, tools, tools_args)
                assert observed['status'] in ('PASS', 'FUNCTION_FAIL'), (ident, observed)
                assert agrees['status'] == 'PASS', (ident, agrees)
                if not is_fault:
                    assert observed['status'] == 'PASS'
                result = dict(id=ident, is_fault=is_fault, spec_test=observed, ir_agreement=agrees)
                results.append(result)
                print(ident+': '+observed['status']+' / agreement '+agrees['status'], flush=True)
                write(out/'rtl-results.partial.json', results)
        summary['rtl_results'] = results
        summary['rtl_faults_missed_by_fixed_tb'] = sum(r['is_fault'] and r['spec_test']['status']=='PASS' for r in results)
        write(out/'summary.json', summary)
    write(out/'evidence-lock.json', {f.relative_to(out).as_posix():sha(f) for f in out.rglob('*') if f.is_file()})
    print('COMPLETE '+json.dumps({k:summary[k] for k in ('total_pairs','faults','equivalent','v2_blindspots')}), flush=True)


if __name__ == '__main__':
    main()

