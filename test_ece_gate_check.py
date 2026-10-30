"""Offline controls only: never count these as school EDA evidence."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import ece_gate_check as gate


class GateCheckTests(unittest.TestCase):
    def test_receipt_requires_complete_nonce_count_exit_and_no_errors(self):
        receipt = 'RTL_LAB_V1 abc checks=1840 errors=0\n'
        self.assertEqual(gate.verdict(receipt, 'abc', 0), 'FIXED_TEST_PASS')
        self.assertEqual(gate.verdict(receipt, 'wrong', 0), 'INVALID_RECEIPT')
        self.assertEqual(gate.verdict(receipt + receipt, 'abc', 0), 'INVALID_RECEIPT')
        self.assertEqual(gate.verdict(receipt, 'abc', 1), 'SIM_ERROR')
        self.assertEqual(gate.verdict(receipt.replace('1840', '1839'), 'abc', 0), 'INCOMPLETE_CHECKS')
        self.assertEqual(gate.verdict(receipt.replace('errors=0', 'errors=1'), 'abc', 0), 'FUNCTION_FAIL')

    def test_model_must_cover_all_mapped_cells_without_substitution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'partial.v').write_text('module DFFR_X1; endmodule')
            with self.assertRaises(ValueError):
                gate.choose_model(root, {'DFFR_X1', 'NOR2_X1'})
            (root / 'complete.v').write_text('module DFFR_X1; endmodule\nmodule NOR2_X1; endmodule')
            model, _ = gate.choose_model(root, {'DFFR_X1', 'NOR2_X1'})
            self.assertEqual(model.name, 'complete.v')

    def test_return_excludes_library_license_and_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'school-test'; work.mkdir()
            for name in ('result.json', 'netlist.v', 'verdict.txt', 'cells.v', 'license.dat', 'simv'):
                (work / name).write_text('offline control')
            gate.collect(work, root / 'share')
            with zipfile.ZipFile(root / 'share' / 'return-school-test.zip') as z:
                self.assertEqual(set(z.namelist()), {'result.json', 'netlist.v', 'verdict.txt'})


if __name__ == '__main__':
    unittest.main()
