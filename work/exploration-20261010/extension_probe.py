"""Construct labeled adversarial extra-state fixtures that pass public examples."""
import copy
import itertools
import json
from pathlib import Path
from types import SimpleNamespace
import compound_probe as probe

bank, old, fsm_ir, lab = probe.bank, probe.old, probe.fsm_ir, probe.lab


def absent_prefix(contract):
    examples = [e['bits'] for e in contract['examples']]
    for length in range(1, max(map(len, examples))+2):
        for bits in map(''.join, itertools.product('01', repeat=length)):
            if not any(example.startswith(bits) for example in examples):
                return bits
    raise AssertionError('No absent prefix')


def extend(reference, bits):
    """Clone the exact prefix path; on divergence fall back to reference states.

    At the unseen prefix endpoint invert the Moore output for that cycle only.
    This is an adversarial fixture construction, not a natural LLM output.
    """
    obj = copy.deepcopy(reference['data'])
    state = reference['reset']['state']
    obj['reset']['state'] = 'T0'
    for i in range(len(bits)+1):
        obj['states'].append(dict(name=f'T{i}', output=reference['outputs'][state] ^ int(i==len(bits))))
        for bit in (0, 1):
            destination = reference['edges'][state, bit]
            if i < len(bits) and bit == int(bits[i]):
                destination = f'T{i+1}'
            obj['transitions'].append({'from':f'T{i}', 'input':bit, 'to':destination})
        if i < len(bits):
            state = reference['edges'][state, int(bits[i])]
    return fsm_ir.parse(old.raw(obj))


def main():
    out = probe.HERE/'evidence-extension-v1'
    if out.exists():
        raise ValueError('Use fresh evidence')
    out.mkdir()
    profile_path = probe.REPO/'evidence/mutation-v1/contracts-v2.json'
    profiles = json.loads(profile_path.read_text(encoding='utf-8'))
    plan = dict(kind='ADVERSARIAL_EXTRA_STATE_PUBLIC_TRACE_BLINDSPOTS', new_model_calls=0,
                cases=5, rtl_evaluations=10, selection='One shortest lexicographic absent public prefix per development family',
                profile_sha256=probe.sha(profile_path), bank_lock_sha256=probe.sha(bank.ROOT/'bank-lock.json'),
                probe_sha256=probe.sha(Path(__file__)), helper_sha256=probe.sha(probe.HERE/'compound_probe.py'),
                source_hashes={n:probe.sha(probe.REPO/n) for n in ('paired_bank.py','mutation_study.py','fsm_ir.py','fsm_checks.py','rtl_lab.py','backends.py','batch.py')},
                scope='Constructed adversarial fixtures, not LLM outputs; no claim of prevalence or benchmark accuracy')
    probe.write(out/'plan.json', plan)
    args = SimpleNamespace(iverilog=None, vvp=None, compile_timeout=15, sim_timeout=10)
    tools = lab.inspect_tools(args, out)
    probe.write(out/'environment.json', tools)
    cases = []
    for spec in old.development_specs():
        task = spec['id']
        reference = bank.graph(task)
        contract = profiles[task]['contract']
        bits = absent_prefix(contract)
        candidate = extend(reference, bits)
        feedback = bank.feedback(old.raw(candidate['data']), contract)
        diagnosis = fsm_ir.product_check(candidate, reference)
        assert feedback['status'] == 'PUBLIC_CHECK_PASS'
        assert diagnosis['status'] == 'IR_SPEC_MISMATCH'
        assert diagnosis['shortest_counterexample']['bits'] == bits
        expected = fsm_ir.trace(reference, bits)
        observed = fsm_ir.trace(candidate, bits)
        assert expected[:-1] == observed[:-1] and expected[-1] != observed[-1]
        witness_inputs = [(0, 0)] + [(1, int(b)) for b in bits]
        assert [r[3] for r in bank.oracle(task, witness_inputs)][1:] == expected
        rtl = bank.fixture_rtl(candidate, spec['ports'], spec['module'])
        folder = out/'rtl'/task
        fixed = old.fixed_sim(folder/'spec', spec, rtl, tools, args)
        witness = old.agreement_sim(folder/'witness', spec, reference, rtl, witness_inputs, tools, args)
        assert fixed['status'] in ('PASS', 'FUNCTION_FAIL'), fixed
        assert witness['status'] == 'FUNCTION_FAIL', witness
        cases.append(dict(task=task, kind='ADVERSARIAL_FIXTURE', reference_states=len(reference['outputs']),
                          candidate_states=len(candidate['outputs']), ir=candidate['data'],
                          public_feedback=feedback, diagnosis=diagnosis, bits=bits,
                          expected=expected, observed=observed, fixed_test=fixed, witness_test=witness))
        print(task+': '+bits+' '+str(expected)+' != '+str(observed)+' fixed '+fixed['status'], flush=True)
        probe.write(out/'cases.partial.json', cases)
    summary = dict(new_model_calls=0, cases=cases, public_pass_but_wrong=len(cases),
                   fixed_test_detected=sum(c['fixed_test']['status']=='FUNCTION_FAIL' for c in cases),
                   witness_reproduced=sum(c['witness_test']['status']=='FUNCTION_FAIL' for c in cases),
                   limit='Deliberately adversarial expanded-state circuits; no estimate of natural model error frequency')
    probe.write(out/'summary.json', summary)
    probe.write(out/'evidence-lock.json', {f.relative_to(out).as_posix():probe.sha(f) for f in out.rglob('*') if f.is_file()})
    print('COMPLETE', flush=True)


if __name__ == '__main__':
    main()
