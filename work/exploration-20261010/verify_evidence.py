"""Independent partition-refinement audit of every compound mutation."""
import itertools
import json
from collections import Counter
from pathlib import Path
import compound_probe as probe


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def graph(obj):
    outputs = {s['name']:s['output'] for s in obj['states']}
    edges = {(e['from'], e['input']):e['to'] for e in obj['transitions']}
    return outputs, edges


def independent_depth(candidate, reference):
    """Color refinement, no calls to product_check/parse/trace/feedback."""
    graphs = [graph(candidate), graph(reference)]
    states = [(side, s) for side, (outputs, _) in enumerate(graphs) for s in outputs]
    color = {(side, s):graphs[side][0][s] for side, s in states}
    start = [(side, obj['reset']['state']) for side, obj in enumerate((candidate, reference))]
    for depth in range(len(states)):
        if color[start[0]] != color[start[1]]:
            return depth
        signatures = {key:(color[key], *(color[side, graphs[side][1][s, b]] for b in (0,1)))
                      for key in states for side, s in [key]}
        labels = {signature:i for i, signature in enumerate(sorted(set(signatures.values())))}
        updated = {key:labels[signatures[key]] for key in states}
        if len(set(updated.values())) == len(set(color.values())):
            return None
        color = updated
    raise AssertionError('Refinement failed to stabilize')


def public_pass(obj, contract):
    outputs, edges = graph(obj)
    if any(obj['reset'][k] != contract['reset'][k] for k in ('kind','active')):
        return False
    if outputs[obj['reset']['state']] != contract['reset']['output']:
        return False
    for ex in contract['examples']:
        state = obj['reset']['state']
        observed = []
        for b in ex['bits']:
            state = edges[state, int(b)]
            observed.append(outputs[state])
        if observed != ex['outputs']:
            return False
    return True


def lock_audit(folder):
    lock = read(folder/'evidence-lock.json')
    files = {p.relative_to(folder).as_posix():probe.sha(p) for p in folder.rglob('*')
             if p.is_file() and p.name != 'evidence-lock.json'}
    assert lock == files, 'Evidence inventory/hash mismatch'
    plan = read(folder/'plan.json')
    for name, digest in plan['source_hashes'].items():
        assert probe.sha(probe.REPO/name) == digest
    assert probe.sha(probe.bank.ROOT/'bank-lock.json') == plan['bank_lock_sha256']
    assert probe.sha(probe.REPO/'evidence/mutation-v1/contracts-v2.json') == plan['profile_sha256']
    return len(lock)


def expected_count(reference, order):
    # Independent combinatorial coefficient of product_locus(1 + alternatives*x).
    loci = Counter(change[0] for _,_,obj in probe.old.mutations(reference)
                   for change in probe.differences(reference['data'], obj))
    coeff = [1]+[0]*order
    for count in loci.values():
        for k in range(order, 0, -1):
            coeff[k] += coeff[k-1]*count
    return coeff[order]


def main():
    specs = {s['id']:s for s in probe.old.development_specs()}
    references = {task:probe.bank.graph(task)['data'] for task in specs}
    profiles = read(probe.REPO/'evidence/mutation-v1/contracts-v2.json')
    audits = []
    for name, order, script in [('evidence-v1',2,'compound_probe.py'),
                                ('evidence-triple-v1',3,'triple_probe.py')]:
        folder = probe.HERE/name
        files = lock_audit(folder)
        plan = read(folder/'plan.json')
        assert probe.sha(probe.HERE/script) == plan['probe_sha256']
        rows = read(folder/'cases.json')
        summary = read(folder/'summary.json')
        counts = Counter()
        unique = set()
        faults = 0
        for row in rows:
            task, obj = row['task'], row['ir']
            reference = references[task]
            assert len(probe.differences(reference, obj)) == order
            signature = (task, probe.old.raw(obj))
            assert signature not in unique
            unique.add(signature)
            counts[task] += 1
            depth = independent_depth(obj, reference)
            metadata = any(obj['reset'][k] != reference['reset'][k] for k in ('kind','active'))
            fault = metadata or depth is not None
            assert fault == row['is_fault']
            ce = row['diagnosis']['shortest_counterexample']
            assert (None if ce is None else len(ce['bits'])) == depth
            assert public_pass(obj, specs[task]['public_contract']) == (row['public_v1']=='PUBLIC_CHECK_PASS')
            assert public_pass(obj, profiles[task]['contract']) == (row['public_v2']=='PUBLIC_CHECK_PASS')
            faults += int(fault)
        assert counts == {task:expected_count(probe.bank.graph(task), order) for task in specs}
        assert len(rows) == summary['total_pairs'] and faults == summary['faults']
        for cov in summary['coverage']:
            selected = [r for r in rows if r['task']==cov['task'] and r['is_fault']]
            assert cov['v1_missed'] == sum(r['public_v1']=='PUBLIC_CHECK_PASS' for r in selected)
            assert cov['v2_missed'] == sum(r['public_v2']=='PUBLIC_CHECK_PASS' for r in selected)
        audits.append(dict(folder=name, status='PASS', independently_checked=len(rows), faults=faults,
                           files=files, method='Independent color refinement, public trace interpreter, combinatorial count and inventory hashes'))
        print(json.dumps(audits[-1]), flush=True)
        del rows, unique
    folder = probe.HERE/'evidence-extension-v1'
    files = lock_audit(folder)
    plan = read(folder/'plan.json')
    assert probe.sha(probe.HERE/'extension_probe.py') == plan['probe_sha256']
    assert probe.sha(probe.HERE/'compound_probe.py') == plan['helper_sha256']
    cases = read(folder/'summary.json')['cases']
    assert len(cases)==5 and {r['task'] for r in cases}==set(specs)
    for row in cases:
        assert public_pass(row['ir'], profiles[row['task']]['contract'])
        assert independent_depth(row['ir'], references[row['task']]) == len(row['bits'])
        assert row['witness_test']['status'] == 'FUNCTION_FAIL'
        assert row['fixed_test']['status'] == 'FUNCTION_FAIL'
        dut = folder/'rtl'/row['task']/'spec/dut.sv'
        assert probe.sha(dut) == row['fixed_test']['rtl_sha256']
        assert dut.read_bytes() == (folder/'rtl'/row['task']/'witness/dut.sv').read_bytes()
    audits.append(dict(folder=folder.name, status='PASS', independently_checked=len(cases), files=files))
    probe.write(probe.HERE/'verification.json',dict(status='PASS',audits=audits,
                new_model_calls=0, verified_variants=44048, verified_extension_cases=5))
    print('ALL AUDITS PASS', flush=True)


if __name__ == '__main__':
    main()
