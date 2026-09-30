"""Independent semantics, real Icarus, budget, and evidence regression tests."""
import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import batch
import fsm_checks as checks
import fsm_ir
import fsm_study as study
import rtl_lab as lab


def rtl_from_ir(ir, task, module):
    """Deliberate test-fixture compiler, never used for real model generation."""
    c = checks.CONTRACTS[task]; r = c['reset_port']; b = c['input_port']; out = c['output_port']
    states = list(ir['outputs']); ids = {s: i for i, s in enumerate(states)}
    active = ir['reset']['active']; sensitivity = 'posedge clk'
    if ir['reset']['kind'] == 'async':
        sensitivity += f" or {'posedge' if active else 'negedge'} {r}"
    cases = '\n'.join(f"{ids[s]}: if({b}) state <= {ids[ir['edges'][s, 1]]}; else state <= {ids[ir['edges'][s, 0]]};" for s in states)
    terms = ' || '.join(f'(state == {ids[s]})' for s in states if ir['outputs'][s]) or "1'b0"
    return f'''module {module}(input clk, input {r}, input {b}, output {out});
reg [4:0] state;
always @({sensitivity}) begin
if ({r} == 1'b{active}) state <= {ids[ir['reset']['state']]};
else case (state)
{cases}
default: state <= {ids[ir['reset']['state']]};
endcase
end
assign {out} = {terms};
endmodule
'''


class FSMTests(unittest.TestCase):
    def setUp(self):
        base = batch.ROOT / 'test-results'; base.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='fsm_', dir=base))
        self.specs = {s['id']: s for s in batch.manifest('dev10')}

    def ir(self, task='rt_sequence'):
        return copy.deepcopy(checks.reference_ir(task)['data'])

    def test_schema_rejects_ambiguous_or_incomplete_data(self):
        for change in ('duplicate', 'missing', 'unknown', 'bool', 'reset', 'too_many'):
            obj = self.ir()
            if change == 'duplicate': obj['transitions'][1] = obj['transitions'][0]
            if change == 'missing': obj['transitions'].pop()
            if change == 'unknown': obj['transitions'][0]['to'] = 'missing'
            if change == 'bool': obj['states'][0]['output'] = True
            if change == 'reset': obj['reset']['state'] = []
            if change == 'too_many': obj['states'] *= 7
            with self.assertRaises(ValueError, msg=change): fsm_ir.parse(json.dumps(obj))
        with self.assertRaises(ValueError): fsm_ir.parse('{"schema":1,"schema":1}')
        with self.assertRaises(ValueError): fsm_ir.parse('[' * 1000)
        with self.assertRaises(ValueError): fsm_ir.parse('x' * 32769)

    def test_state_renaming_and_redundancy_do_not_change_semantics(self):
        obj = self.ir(); renamed = json.dumps(obj)
        for n in range(5): renamed = renamed.replace('S' + str(n), 'q_' + str(9 - n))
        candidate = fsm_ir.parse(renamed)
        self.assertEqual(fsm_ir.product_check(candidate, checks.reference_ir('rt_sequence'))['status'], 'IR_EQUIVALENT')
        obj['states'].append(dict(name='unused', output=1))
        obj['transitions'] += [{'from': 'unused', 'input': b, 'to': 'unused'} for b in (0, 1)]
        self.assertEqual(checks.private_check(json.dumps(obj), 'rt_sequence')['status'], 'IR_EQUIVALENT')

    def test_public_is_not_private_and_counterexample_is_replayable(self):
        obj = self.ir()
        # Break only the fallback after a match followed by 1. Public traces
        # intentionally do not cover every edge/context.
        next(e for e in obj['transitions'] if e['from'] == 'S4' and e['input'] == 1)['to'] = 'S0'
        raw = json.dumps(obj)
        self.assertEqual(checks.public_check(raw, 'rt_sequence')['status'], 'PUBLIC_CHECK_PASS')
        diagnosis = checks.private_check(raw, 'rt_sequence')
        self.assertEqual(diagnosis['status'], 'IR_SPEC_MISMATCH')
        ce = diagnosis['shortest_counterexample']; self.assertIsNotNone(ce)
        self.assertNotEqual(fsm_ir.trace(fsm_ir.parse(raw), ce['bits'])[-1],
                            fsm_ir.trace(checks.reference_ir('rt_sequence'), ce['bits'])[-1])

    def test_oracle_matches_every_frozen_vector(self):
        for task in checks.CONTRACTS:
            directory = batch.ROOT / batch.SUITES['dev10']; spec = self.specs[task]
            rows = fsm_ir.timed_vectors(checks.reference_ir(task), checks.inputs_from_dev(directory, spec))
            words = [int(w, 16) for w in (directory / (task + '.hex')).read_text().split()]
            self.assertEqual(len(rows) * 2, spec['checks'])
            for (_, _, pre, post), word in zip(rows, words):
                self.assertEqual((pre, post), ((word >> 2) & 1, (word >> 1) & 1))
            self.assertEqual(checks.public_check(json.dumps(self.ir(task)), task)['status'], 'PUBLIC_CHECK_PASS')

    def test_timed_reset_and_output_latency_mutations(self):
        reference = checks.reference_ir('rt_sequence')
        obj = self.ir(); obj['reset']['kind'] = 'sync'; sync = fsm_ir.parse(json.dumps(obj))
        inputs = [(0, 0)] + [(1, int(b)) for b in '1001'] + [(0, 0)]
        self.assertEqual(fsm_ir.timed_vectors(reference, inputs)[-1][2:], (0, 0))
        self.assertEqual(fsm_ir.timed_vectors(sync, inputs)[-1][2:], (1, 0))
        self.assertEqual(fsm_ir.product_check(sync, reference)['reset_contract_errors'], ['kind'])
        obj = self.ir(); obj['states'][3]['output'] = 1; obj['states'][4]['output'] = 0
        diag = checks.private_check(json.dumps(obj), 'rt_sequence')
        self.assertEqual(diag['shortest_counterexample']['bits'], '100')

    def test_prompts_have_equal_public_information_and_no_private_feedback(self):
        spec = self.specs['rt_sequence']; raw = json.dumps(self.ir()); public = checks.public_contract(spec['id'])
        for arm in study.ARMS:
            first = study.prompts(spec, arm, public)
            second = study.prompts(spec, arm, public, raw)
            self.assertIn(spec['spec'], first); self.assertIn(spec['spec'], second)
            self.assertIn('1001001', first); self.assertIn('1001001', second)
            self.assertNotIn('shortest_counterexample', second)
            self.assertEqual('PUBLIC_CHECK_PASS' in second, arm == 'checked_table')
        self.assertEqual(study.prompts(spec, 'table', public), study.prompts(spec, 'checked_table', public))

    def test_real_simulation_localizes_deliberate_faults(self):
        task = 'rt_sequence'; spec = self.specs[task]; good = self.ir(); wrong = self.ir()
        next(e for e in wrong['transitions'] if e['from'] == 'S2' and e['input'] == 0)['to'] = 'S0'
        args = SimpleNamespace(iverilog=None, vvp=None, compile_timeout=15, sim_timeout=10)
        tools = lab.inspect_tools(args, self.root)
        for name, ir, rtl_ir, expected in [
            ('correct', good, good, 'ALL_PASS'),
            ('understanding', wrong, wrong, 'SPEC_TO_IR_ERROR'),
            ('implementation', good, wrong, 'IR_TO_RTL_ERROR'),
            ('correction', wrong, good, 'RTL_CORRECTS_IR_ON_TESTS')]:
            folder = self.root / name; folder.mkdir()
            rtl = rtl_from_ir(fsm_ir.parse(json.dumps(rtl_ir)), task, spec['module'])
            row = study.evaluate_rtl(folder, spec, rtl, json.dumps(ir), 'table', tools, args)
            self.assertEqual(row['localization'], expected, row)
            self.assertTrue(row['diagnostic_consistent'])
        sync = self.ir(); sync['reset']['kind'] = 'sync'
        folder = self.root / 'reset'; folder.mkdir()
        row = study.evaluate_rtl(folder, spec, rtl_from_ir(fsm_ir.parse(json.dumps(sync)), task, spec['module']),
                                 json.dumps(good), 'table', tools, args)
        self.assertEqual(row['localization'], 'IR_TO_RTL_ERROR')
        self.assertTrue(any(m['phase'] == 'pre' for m in row['spec_diagnostic']['mismatches']))

    def config(self, max_calls=12):
        config = batch.read(batch.ROOT / 'experiments/fsm48.json')
        config.update(models=['fixture-model'], repeats=1, max_calls=max_calls)
        path = self.root / 'config.json'; batch.atomic(path, config)
        return path

    def test_budget_is_reserved_in_pairs_and_never_reissued(self):
        run = self.root / 'budget'
        with contextlib.redirect_stdout(io.StringIO()): study.init(run, self.config(3))
        plan = study.read_plan(run)
        self.assertTrue(study.reserve(run, plan['jobs'][0], plan))
        self.assertFalse(study.reserve(run, plan['jobs'][1], plan))
        with self.assertRaises(ValueError): study.reserve(run, plan['jobs'][0], plan)
        summary = study.report(run)
        self.assertEqual(summary['model_call_reservations'], 2)
        self.assertEqual(summary['model_turns_started'], 0)
        self.assertEqual(summary['real_generations'], 0)
        batch.atomic(run / 'plan.json', dict(plan, max_calls=100))
        with self.assertRaises(ValueError): study.read_plan(run)

    def test_offline_roundtrip_resume_csv_and_curated_hashes(self):
        run = self.root / 'offline'
        with contextlib.redirect_stdout(io.StringIO()):
            study.init(run, self.config(), 'offline')
            self.assertEqual(study.run_jobs(run, workers=2), 0)
            before = (run / 'summary.json').read_bytes()
            self.assertEqual(study.run_jobs(run, workers=2), 0)
            self.assertEqual(before, (run / 'summary.json').read_bytes())
            study.curate(run, self.root / 'evidence')
        summary = study.report(run)
        self.assertEqual(summary['completed'], 6)
        self.assertEqual(sum(g['passes'] for g in summary['groups']), 6)
        self.assertEqual(summary['real_generations'], 0)
        self.assertEqual(summary['model_call_reservations'], 0)
        self.assertEqual(summary['model_turns_started'], 0)
        with (run / 'summary.csv').open(encoding='utf-8-sig', newline='') as f:
            self.assertEqual(len(list(csv.reader(f))), 7)
        for name, sha in batch.read(self.root / 'evidence/evidence-lock.json').items():
            self.assertEqual(lab.digest((self.root / 'evidence' / name).read_bytes()), sha)
        for p in (self.root / 'evidence').rglob('*'):
            self.assertNotIn('auth', p.name); self.assertNotEqual(p.suffix, '.log')

    def test_interrupted_job_is_terminal_and_source_changes_block_resume(self):
        run = self.root / 'interrupt'
        with contextlib.redirect_stdout(io.StringIO()): study.init(run, self.config(), 'offline')
        plan = study.read_plan(run); job = plan['jobs'][0]
        study.reserve(run, job, plan)
        with contextlib.redirect_stdout(io.StringIO()): study.run_jobs(run, workers=1, max_jobs=0)
        self.assertEqual(batch.latest(run, job)['status'], 'INTERRUPTED')
        self.assertFalse((run / 'jobs' / job['id'] / 'stage1').exists())
        plan['source_hashes']['fsm_ir.py'] = 'bad'; batch.atomic(run / 'plan.json', plan)
        batch.atomic(run / 'study-lock.json', dict(plan_sha256=lab.digest((run / 'plan.json').read_bytes())))
        with self.assertRaises(ValueError): study.read_plan(run, check_source=True)


if __name__ == '__main__': unittest.main()
