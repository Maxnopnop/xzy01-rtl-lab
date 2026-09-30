import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import batch
import fsm_ir
import mutation_study as mutation
import paired_bank as bank
import paired_study as study
import rtl_lab as lab


class MutationTests(unittest.TestCase):
    def test_all_declared_single_edits_and_no_heldout(self):
        data=mutation.analyze()
        self.assertEqual(len(data['cases']),163)
        self.assertFalse({r['task'] for r in data['cases']} & set(bank.HELDOUT))
        for spec in mutation.development_specs():
            original=bank.graph(spec['id'])['data']; n=len(original['states'])
            selected=[r for r in data['cases'] if r['task']==spec['id']]
            self.assertEqual(len(selected),2*n*(n-1)+n+2+n-1)
            self.assertEqual(len({mutation.raw(r['ir']) for r in selected}),len(selected))
            for row in selected:
                a=original;b=row['ir']
                changed=sum(x!=y for x,y in zip(a['transitions'],b['transitions']))+sum(x!=y for x,y in zip(a['states'],b['states']))+int(a['reset']!=b['reset'])
                self.assertEqual(changed,1)
                self.assertEqual(fsm_ir.product_check(fsm_ir.parse(mutation.raw(b)),bank.graph(spec['id']))['status'],'IR_SPEC_MISMATCH')

    def test_blind_spots_removed_without_changing_original_contracts(self):
        original=copy.deepcopy([s['public_contract'] for s in mutation.development_specs()])
        data=mutation.analyze()
        self.assertEqual(sum(c['public_misses_before'] for c in data['coverage']),30)
        self.assertEqual(sum(c['public_misses_after'] for c in data['coverage']),0)
        self.assertEqual(data,mutation.analyze())
        self.assertEqual(original,[s['public_contract'] for s in mutation.development_specs()])
        for spec in mutation.development_specs():
            self.assertEqual(mutation.check_public(data['contracts'],spec['id'],mutation.raw(bank.graph(spec['id'])['data']))['status'],'PUBLIC_CHECK_PASS')

    def test_public_checker_has_no_private_oracle_dependency(self):
        data=mutation.analyze();case=next(r for r in data['cases'] if r['public_before']=='PUBLIC_CHECK_PASS')
        with patch.object(bank,'load',side_effect=AssertionError('private load')),patch.object(bank,'graph',side_effect=AssertionError('private graph')),patch.object(bank,'oracle',side_effect=AssertionError('private oracle')):
            self.assertEqual(mutation.check_public(data['contracts'],case['task'],mutation.raw(case['ir']))['status'],'PUBLIC_CHECK_FAIL')
        with self.assertRaises(ValueError):mutation.check_public(data['contracts'],'unknown','{}')

    def test_actual_icarus_all_diagnostic_quadrants(self):
        spec=next(s for s in mutation.development_specs() if s['id']=='request_delay')
        reference=bank.graph(spec['id']);obj=copy.deepcopy(reference['data']);obj['states'][0]['output']^=1
        first=fsm_ir.parse(json.dumps(obj));obj=copy.deepcopy(reference['data']);obj['states'][1]['output']^=1
        second=fsm_ir.parse(json.dumps(obj))
        cases=[(reference,reference,'ALL_PASS'),(first,first,'SPEC_TO_IR_ERROR'),
               (reference,first,'IR_TO_RTL_ERROR'),(first,reference,'RTL_CORRECTS_IR_ON_TESTS'),(first,second,'BOTH_DIVERGE')]
        args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=10)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tools=lab.inspect_tools(args,root)
            for index,(ir,rtl_ir,expected) in enumerate(cases):
                folder=root/str(index);folder.mkdir()
                result=study.judge(folder,spec,bank.fixture_rtl(rtl_ir,spec['ports'],spec['module']),mutation.raw(ir['data']),tools,args)
                self.assertEqual(result['localization'],expected)
                self.assertTrue(result['diagnostic_consistent'])

    def test_evidence_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'cases.json').write_bytes(b'original')
            batch.atomic(root/'evidence-lock.json',{'cases.json':lab.digest(b'original')})
            (root/'cases.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Evidence changed'):mutation.verify(root)


if __name__=='__main__':unittest.main()
