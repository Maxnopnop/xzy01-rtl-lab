"""Synthetic transport evidence only; never a real DC or Genus result."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import ece_synthesis as bridge
import ece_synth_school as school
import ece_synth_common as common


class SynthesisBridgeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.run = self.root / 'run'
        self.state = self.root / 'state'
        self.shared = self.root / 'shared'
        self.config = self.root / 'config.json'
        common.save(self.config, common.template())
        dut = self.run / 'jobs/case/attempt/dut.sv'
        dut.parent.mkdir(parents=True)
        dut.write_bytes((bridge.ROOT / 'examples/correct/adder8.sv').read_bytes())
        common.save(self.run / 'plan.json', dict(tasks=[dict(id='adder8', module='adder8')], jobs=[dict(id='case', task='adder8')]))
        common.save(self.run / 'jobs/case/result.json', dict(status='PASS', directory='jobs/case/attempt', rtl_sha256=common.sha(dut)))

    def package(self, tool='dc', ready=False):
        if ready:
            settings = common.template()
            sdc = self.root / 'fixture.sdc'
            sdc.write_bytes(b'# SYNTHETIC CONSTRAINT FIXTURE\r\nset_max_delay 5 -from [all_inputs] -to [all_outputs]\r\n')
            settings['tools'][tool].update(libraries=['/fixture/stdcells.' + ('db' if tool == 'dc' else 'lib')],
                corner='SYNTHETIC_NOT_A_PDK', sdc_file=str(sdc), constraints_reviewed=True)
            common.save(self.config, settings)
        return bridge.pack(self.run, 'case', tool, self.config, self.shared, self.state)

    def attempt(self, row):
        target = self.root / ('attempt-' + row['tool'])
        shutil.copytree(row['package_dir'], target)
        return target

    def complete_fixture(self, folder, code=0):
        job = common.verify(folder)
        common.save(folder / 'execution.json', dict(package_id=job['package_id'], nonce=job['nonce'], tool=job['tool'], status='EXITED', returncode=code))
        common.save(folder / 'doctor.json', dict(tool=job['tool'], sdc_sha256=job['sdc_sha256'], missing=[], libraries=[dict(path=p, readable=True, sha256='a'*64) for p in job['profile']['libraries']]))
        for name in common.REQUIRED + ('tool.log', 'tool_version.log', 'reports/check_design.rpt'):
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('SYNTHETIC_NOT_COMMERCIAL_TOOL\n')
        (folder / 'receipt.txt').write_text('XZY01_SYNTH_V1 ' + job['nonce'] + ' COMPLETE\n')

    def return_and_import(self, folder):
        school.collect(folder)
        school.ship(folder, self.shared / 'inbox')
        return bridge.ingest(self.shared, self.state)

    def test_missing_library_blocks_before_any_tool_and_returns(self):
        row = self.package()
        attempt = self.attempt(row)
        with patch.object(school.subprocess, 'Popen', side_effect=AssertionError('Must not start EDA')):
            self.assertEqual(school.run(attempt), 2)
        self.assertIn('standard-cell library paths', common.read(attempt / 'doctor.json')['missing'])
        self.assertEqual(self.return_and_import(attempt), 0)
        self.assertEqual(bridge.report(self.state)[0]['status'], 'BLOCKED_PREREQUISITES')
        with self.assertRaises(ValueError): school.run(attempt)
        competing = self.root / 'competing'
        shutil.copytree(row['package_dir'], competing)
        (competing / '.run-reserved').write_text('existing process')
        with patch.object(school.subprocess, 'Popen', side_effect=AssertionError('No concurrent EDA')):
            with self.assertRaises(FileExistsError): school.run(competing)

    def test_complete_two_tools_separate_from_pass_and_dedup(self):
        for tool in ('dc', 'genus'):
            row = self.package(tool, ready=True)
            attempt = self.attempt(row)
            self.complete_fixture(attempt)
            self.assertEqual(self.return_and_import(attempt), 0)
        self.assertEqual(bridge.ingest(self.shared, self.state), 0)
        rows = bridge.report(self.state)
        self.assertEqual({r['tool'] for r in rows}, {'dc', 'genus'})
        self.assertTrue(all(r['status'] == 'COMPLETED_REVIEW_REQUIRED' and r['attempts'] == 1 for r in rows))

    def test_zero_exit_without_artifacts_and_nonzero_are_not_pass(self):
        row = self.package(ready=True)
        attempt = self.attempt(row)
        self.complete_fixture(attempt)
        (attempt / 'outputs/netlist.v').unlink()
        self.assertEqual(bridge.judge(attempt, Path(row['package_dir'])), 'OUTPUT_INCOMPLETE')
        self.complete_fixture(attempt, code=1)
        self.assertEqual(bridge.judge(attempt, Path(row['package_dir'])), 'TOOL_FAILED')

    def test_receipt_and_original_source_tamper_rejected(self):
        row = self.package('genus', ready=True)
        attempt = self.attempt(row)
        self.complete_fixture(attempt)
        (attempt / 'receipt.txt').write_text('fake receipt')
        with self.assertRaises(ValueError): bridge.judge(attempt, Path(row['package_dir']))
        self.complete_fixture(attempt)
        (attempt / 'dut.sv').write_text('CHANGED')
        with self.assertRaises(ValueError): bridge.judge(attempt, Path(row['package_dir']))

    def test_menu_rejects_multi_select_and_only_dispatches_one(self):
        row = self.package()
        with patch('builtins.input', return_value='1,2'), patch.object(school.subprocess, 'call', side_effect=AssertionError('No call')):
            with self.assertRaises(ValueError): school.menu(self.shared, work=self.root / 'school')
        with patch.object(school.subprocess, 'call', return_value=2) as call:
            self.assertEqual(school.menu(self.shared, row['package_id'], self.root / 'school'), 2)
            self.assertEqual(call.call_count, 1)

    def test_input_hashes_and_library_bytes_not_packaged(self):
        row = self.package(ready=True)
        folder = Path(row['package_dir'])
        job = common.verify(folder)
        self.assertEqual((folder / 'constraints.sdc').read_bytes(), (self.root / 'fixture.sdc').read_bytes())
        self.assertEqual(job['source_result_sha256'], common.sha(self.run / 'jobs/case/result.json'))
        with zipfile.ZipFile(self.shared / row['archive']) as z:
            self.assertEqual(set(z.namelist()), common.INPUTS | {'payload-lock.json'})
            self.assertFalse(any(n.endswith(('.lib', '.db')) for n in z.namelist()))
        before = (self.run / 'jobs/case/attempt/dut.sv').read_bytes()
        bridge.report(self.state)
        self.assertEqual((self.run / 'jobs/case/attempt/dut.sv').read_bytes(), before)

    def test_zip_traversal_and_corrupt_return_rejected(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as z: z.writestr('../outside.txt', 'bad')
        with self.assertRaises(ValueError): common.extract(archive, self.root / 'unpack', common.INPUTS)
        row = self.package(ready=True)
        attempt = self.attempt(row)
        self.complete_fixture(attempt)
        school.collect(attempt)
        school.ship(attempt, self.shared / 'inbox')
        next((self.shared / 'inbox').glob('*.zip')).write_bytes(b'CORRUPT')
        self.assertEqual(bridge.ingest(self.shared, self.state), 1)
        self.assertEqual(len(bridge.registry(self.state)['imports']), 0)

    def test_library_strings_are_quoted_and_source_change_stops_pack(self):
        settings = common.template()['tools']['dc']
        settings['libraries'] = ['/library/a[$evil];x.db']
        script = common.tcl('dc', 'adder8', settings, 'a'*32)
        self.assertIn('a\\[\\$evil\\];x.db', script)
        (self.run / 'jobs/case/attempt/dut.sv').write_text('changed')
        with self.assertRaises(ValueError): self.package()


if __name__ == '__main__':
    unittest.main()
