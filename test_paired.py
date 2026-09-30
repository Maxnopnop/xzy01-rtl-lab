"""Fixed-bank independence, matched information, and one-call budget tests."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import backends
import batch
import fsm_checks
import fsm_ir
import paired_bank as bank
import paired_study as study
import rtl_lab as lab


class PairedTests(unittest.TestCase):
    def setUp(self):
        root=batch.ROOT/'test-results'; root.mkdir(exist_ok=True)
        self.root=Path(tempfile.mkdtemp(prefix='paired_',dir=root)); self.data=bank.load()

    def test_bank_oracle_exhaustive_prefixes_and_heldout_split(self):
        self.assertEqual(len(self.data['cases']),12)
        self.assertFalse(set(self.data['split']['development']) & set(self.data['split']['heldout']))
        self.assertFalse({c['task'] for c in self.data['cases']} & set(bank.HELDOUT))
        for spec in self.data['tasks']:
            inputs=batch.read(bank.ROOT/spec['id']/'inputs.json')
            self.assertEqual(fsm_ir.timed_vectors(bank.graph(spec['id']),inputs),bank.oracle(spec['id'],inputs))
            self.assertEqual(bank.feedback(json.dumps(bank.graph(spec['id'])['data']),spec['public_contract'])['status'],'PUBLIC_CHECK_PASS')

    def test_natural_ir_exact_bytes_and_all_faults_non_equivalent(self):
        real=next(c for c in self.data['cases'] if c['kind']=='REAL_RETAINED_IR')
        self.assertEqual((batch.ROOT/real['origin']).read_bytes(),(bank.ROOT/real['ir_file']).read_bytes())
        for case in self.data['cases']:
            candidate=fsm_ir.parse((bank.ROOT/case['ir_file']).read_text(encoding='utf-8'))
            self.assertEqual(fsm_ir.product_check(candidate,bank.graph(case['task']))['status'],'IR_SPEC_MISMATCH')

    def test_only_public_feedback_differs_between_paired_prompts(self):
        for case in self.data['cases']:
            spec=next(s for s in self.data['tasks'] if s['id']==case['task'])
            raw=(bank.ROOT/case['ir_file']).read_text(encoding='utf-8')
            control=study.prompt(spec,raw,'control'); treatment=study.prompt(spec,raw,'feedback')
            chunk='\nExecutable results on the already-public contract:\n'+json.dumps(bank.feedback(raw,spec['public_contract']),indent=2)+'\n'
            self.assertEqual(treatment.replace(chunk,''),control)
            self.assertNotIn('shortest_counterexample',treatment)
            self.assertIn(raw,control)

    def test_real_icarus_reference_and_every_wrong_fixture(self):
        args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10)
        tools=lab.inspect_tools(args,self.root)
        for spec in self.data['tasks']:
            folder=self.root/('reference_'+spec['id']); folder.mkdir()
            source=bank.ROOT/spec['id']; (folder/'dut.sv').write_bytes((source/'reference.sv').read_bytes())
            for name in ('testbench.sv',*spec['assets']): (folder/name).write_bytes((source/name).read_bytes())
            self.assertEqual(backends.IcarusBackend().evaluate(folder,spec,tools,args)['status'],'PASS',spec['id'])
        for case in self.data['cases']:
            spec=next(s for s in self.data['tasks'] if s['id']==case['task'])
            raw=(bank.ROOT/case['ir_file']).read_text(encoding='utf-8'); folder=self.root/case['id']; folder.mkdir()
            rtl=bank.fixture_rtl(fsm_ir.parse(raw),spec['ports'],spec['module'])
            row=study.judge(folder,spec,rtl,raw,tools,args)
            self.assertEqual(row['status'],'FUNCTION_FAIL',case['id'])
            self.assertEqual(row['localization'],'SPEC_TO_IR_ERROR',row)

    def test_plan_budget_and_stage_gate(self):
        run=self.root/'a'
        with contextlib.redirect_stdout(io.StringIO()): study.init(run,'A')
        plan=study.read_plan(run); self.assertEqual(plan['max_calls'],32)
        for job in plan['jobs']: self.assertTrue(study.reserve(run,job,plan))
        self.assertEqual(study.report(run)['model_call_reservations'],32)
        extra=dict(plan['jobs'][0],id='extra')
        self.assertFalse(study.reserve(run,extra,plan))
        with self.assertRaises(ValueError): study.reserve(run,plan['jobs'][0],plan)
        with self.assertRaises(ValueError): study.init(self.root/'b','B',previous=run)
        self.assertEqual(study.report(run)['real_generations'],0)

    def test_offline_roundtrip_no_duplicates_and_curation(self):
        run=self.root/'offline'
        with contextlib.redirect_stdout(io.StringIO()):
            study.init(run,'A','offline',1); self.assertEqual(study.run_jobs(run),0)
            original=(run/'summary.json').read_bytes(); self.assertEqual(study.run_jobs(run),0)
            self.assertEqual(original,(run/'summary.json').read_bytes())
            study.curate(run,self.root/'evidence')
        summary=study.report(run)
        self.assertEqual(summary['completed'],16); self.assertEqual(summary['real_generations'],0)
        self.assertEqual(summary['pair_counts'],{'both_pass':8})
        for name,sha in batch.read(self.root/'evidence/evidence-lock.json').items():
            self.assertEqual(lab.digest((self.root/'evidence'/name).read_bytes()),sha)

    def test_interruption_and_plan_tamper_are_closed(self):
        run=self.root/'interrupt'
        with contextlib.redirect_stdout(io.StringIO()): study.init(run,'A','offline',1)
        plan=study.read_plan(run); study.reserve(run,plan['jobs'][0],plan)
        with contextlib.redirect_stdout(io.StringIO()): study.run_jobs(run,max_jobs=0)
        self.assertEqual(batch.latest(run,plan['jobs'][0])['status'],'INTERRUPTED')
        plan['max_calls']=999; batch.atomic(run/'plan.json',plan)
        with self.assertRaises(ValueError): study.read_plan(run)


if __name__=='__main__': unittest.main()
