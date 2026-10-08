"""Transport and launcher tests; synthetic receipts are NOT real commercial runs."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import warnings
from unittest.mock import patch
import ece_desktop as desktop
import ece_transfer as transfer
import school_bridge


class TransportTests(unittest.TestCase):
    def test_vcs_reads_harness_timescale_before_dut(self):
        script=school_bridge.script('vcs','abc123')
        self.assertIn('-top tb testbench.sv dut.sv',script)
        self.assertNotIn('-top tb dut.sv testbench.sv',script)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.package = self.root / 'package'; self.package.mkdir()
        self.case = 'test_case'; source = self.package / self.case; source.mkdir()
        (source / 'dut.sv').write_text('SYNTHETIC_TEST_SOURCE')
        self.meta = dict(job_id=self.case, task='test', backend='vcs', original_status='PASS',
                         nonce='abc123', checks=1, hashes={'dut.sv': desktop.digest(source / 'dut.sv')})
        (source / 'case.json').write_text(json.dumps(self.meta))
        (source / 'run_vcs.csh').write_text('SYNTHETIC_TEST_ONLY')
        (self.package / 'package.json').write_text(json.dumps(dict(cases=[self.meta], backend='vcs')))
        lock = {p.relative_to(self.package).as_posix(): desktop.digest(p) for p in self.package.rglob('*') if p.is_file()}
        (self.package / 'transfer-lock.json').write_text(json.dumps(lock))

    def test_lock_rejects_modified_script(self):
        desktop.verify(self.package)
        (self.package / self.case / 'run_vcs.csh').write_text('changed')
        with self.assertRaises(ValueError): desktop.verify(self.package)

    def test_rejects_unsafe_duplicate_and_symlink_zip(self):
        for i, name in enumerate(('../evil','/evil','test_case\\evil','test_case/unknown','C:/evil')):
            archive = self.root / ('bad%d.zip' % i)
            with zipfile.ZipFile(archive,'w') as z: z.writestr(name,'bad')
            with self.assertRaises(ValueError): transfer.extract_return(archive,self.root / ('out%d'%i),desktop.verify(self.package))
            self.assertFalse((self.root / ('out%d'%i)).exists())
        archive=self.root/'link.zip'
        with zipfile.ZipFile(archive,'w') as z:
            member=zipfile.ZipInfo('test_case/dut.sv'); member.external_attr=0o120777<<16; z.writestr(member,'/etc/passwd')
        with self.assertRaises(ValueError): transfer.extract_return(archive,self.root/'linkout',desktop.verify(self.package))
        archive=self.root/'duplicate.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('test_case/dut.sv','one'); z.writestr('test_case/dut.sv','two')
        with self.assertRaises(ValueError): transfer.extract_return(archive,self.root/'dupout',desktop.verify(self.package))

    def test_stage_does_not_overwrite(self):
        archive=self.root/'a.zip'; archive.write_bytes(b'test')
        with contextlib.redirect_stdout(io.StringIO()): transfer.stage(archive,self.root/'shared')
        with self.assertRaises(FileExistsError): transfer.stage(archive,self.root/'shared')

    def test_empty_return_is_not_verified(self):
        archive=self.root/'empty.zip'
        with zipfile.ZipFile(archive,'w'): pass
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(transfer.receive(self.package,archive,self.root/'empty'),1)
        self.assertEqual(json.loads((self.root/'empty/import-report.json').read_text())['results'][0]['status'],'NOT_RUN')

    def test_collect_import_and_timeout_override(self):
        folder=self.package/'results'/self.case/'attempt'; folder.mkdir(parents=True)
        for p in (self.package/self.case).iterdir(): (folder/p.name).write_bytes(p.read_bytes())
        contents={'execution.json':json.dumps(dict(status='EXITED',returncode=0)), 'launcher.log':'SYNTHETIC_TEST',
                  'tool_version.log':'SYNTHETIC_NOT_VCS','compile.log':'test','simulate.log':'test',
                  'compile.exit':'0','simulate.exit':'0','verdict.txt':'RTL_LAB_V1 abc123 checks=1 errors=0\n'}
        for name, value in contents.items(): (folder/name).write_text(value)
        with contextlib.redirect_stdout(io.StringIO()):
            archive=self.root/'return.zip'; desktop.collect(self.package,self.case,'attempt',archive)
            self.assertEqual(transfer.receive(self.package,archive,self.root/'received'),0)
            self.assertEqual(json.loads((self.root/'received/import-report.json').read_text())['results'][0]['status'],'PASS')
            (folder/'execution.json').write_text(json.dumps(dict(status='TIMEOUT',returncode=-15)))
            archive=self.root/'timeout.zip'; desktop.collect(self.package,self.case,'attempt',archive)
            self.assertEqual(transfer.receive(self.package,archive,self.root/'timedout'),1)
        with self.assertRaises(ValueError): desktop.collect(self.package,self.case,'../escape',self.root/'bad.zip')

    def test_runner_runs_one_case_in_new_attempt(self):
        with patch.object(desktop.os,'name','posix'), patch.object(desktop.shutil,'which',return_value='/mock/tcsh'), patch.object(desktop.subprocess,'Popen') as proc:
            proc.return_value.wait.return_value=0
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(desktop.run_case(self.package,self.case),0)
            self.assertEqual(proc.call_count,1)
            command=proc.call_args[0][0]
            self.assertEqual(command[0],'tcsh')
            working_directory=proc.call_args[1]['cwd']
            self.assertEqual(len(list((self.package/'results'/self.case).iterdir())),1)
        self.assertTrue(Path(command[1]).is_absolute())
        self.assertEqual(Path(command[1]).name,'run_vcs.csh')
        self.assertEqual(Path(command[1]).parent,Path(working_directory))
        with self.assertRaises(ValueError): desktop.case_meta(self.package,'test_case,other')


if __name__ == '__main__': unittest.main()
