"""End-to-end transport fixtures are synthetic; never commercial simulation evidence."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import ece_desktop as desktop
import ece_station as station
import ece_workflow as workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.state=self.root/'state';self.shared=self.root/'shared';self.shared.mkdir()
        self.package=self.root/'package';self.package.mkdir();self.case='test_case'
        folder=self.package/self.case;folder.mkdir()
        (folder/'dut.sv').write_text('SYNTHETIC_TEST_SOURCE')
        self.meta=dict(job_id=self.case,task='test',backend='vcs',original_status='PASS',nonce='abc123',checks=1,
                       hashes={'dut.sv':desktop.digest(folder/'dut.sv')})
        (folder/'case.json').write_text(json.dumps(self.meta))
        (self.package/'package.json').write_text(json.dumps(dict(backend='vcs',cases=[self.meta])))
        (self.package/'ece_desktop.py').write_bytes((workflow.ROOT/'ece_desktop.py').read_bytes())
        lock={p.relative_to(self.package).as_posix():desktop.digest(p) for p in self.package.rglob('*') if p.is_file()}
        (self.package/'transfer-lock.json').write_text(json.dumps(lock))
        (self.package/'station-provenance.json').write_text(json.dumps(dict(package_id='pack',archive_sha256='sourcehash')))
        self.entry=dict(package_id='pack',archive='package.zip',archive_sha256='sourcehash',backend='vcs',label='fixture',
                       run_dir='synthetic-run',package_dir=str(self.package),shared_dir=str(self.shared),
                       cases=[dict(job_id=self.case,task='test',original_status='PASS')])
        workflow.saved(self.state/'registry.json',dict(schema=1,packages=[self.entry],imports=[]))

    def attempt(self,status='EXITED',code=0):
        target=self.package/'results'/self.case/'attempt';target.mkdir(parents=True)
        shutil.copyfile(self.package/self.case/'dut.sv',target/'dut.sv')
        shutil.copyfile(self.package/self.case/'case.json',target/'case.json')
        contents={'execution.json':json.dumps(dict(case=self.case,backend='vcs',status=status,returncode=code)),
                  'launcher.log':'SYNTHETIC_TEST','tool_version.log':'SYNTHETIC_NOT_VCS',
                  'compile.log':'test','simulate.log':'test','compile.exit':'0','simulate.exit':'0',
                  'verdict.txt':'RTL_LAB_V1 abc123 checks=1 errors=0\n'}
        for n,v in contents.items():(target/n).write_text(v)
        return target

    def return_fixture(self,status='EXITED',code=0):
        target=self.attempt(status,code)
        with patch.object(desktop,'run_case',return_value=(code,target)) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                result=desktop.run_return(self.package,self.case,self.shared/'inbox')
            self.assertEqual(run.call_count,1)
        return result

    def test_single_case_auto_return_import_and_dedup(self):
        self.assertEqual(self.return_fixture(),0)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(workflow.ingest(self.shared,self.state),0)
            self.assertEqual(workflow.ingest(self.shared,self.state),0)
        reg=workflow.registry(self.state);self.assertEqual(len(reg['imports']),1)
        self.assertEqual(reg['imports'][0]['results'][0]['status'],'PASS')
        self.assertTrue((self.state/'report.html').exists())

    def test_timeout_does_not_become_pass(self):
        self.assertEqual(self.return_fixture('TIMEOUT',-15),-15)
        with contextlib.redirect_stdout(io.StringIO()):workflow.ingest(self.shared,self.state)
        self.assertEqual(workflow.registry(self.state)['imports'][0]['results'][0]['status'],'SIM_ERROR')

    def test_return_failure_preserves_outbox_and_ship_retries_without_eda(self):
        target=self.attempt()
        with patch.object(desktop,'run_case',return_value=(0,target)),patch.object(desktop,'ship',side_effect=OSError('shared offline')):
            with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(desktop.run_return(self.package,self.case,self.shared/'inbox'),2)
        self.assertEqual(len(list((self.package/'outbox').glob('*.zip'))),1)
        with contextlib.redirect_stdout(io.StringIO()):
            desktop.ship(self.package,self.shared/'inbox');desktop.ship(self.package,self.shared/'inbox')
        self.assertEqual(len(list((self.shared/'inbox').glob('*.json'))),1)

    def test_corrupt_or_unknown_return_rejected(self):
        self.return_fixture()
        sidecar=next((self.shared/'inbox').glob('*.json'));info=workflow.read(sidecar)
        info['package_sha256']='wrong';workflow.saved(sidecar,info)
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(workflow.ingest(self.shared,self.state),1)
        self.assertEqual(len(workflow.registry(self.state)['imports']),0)

    def test_station_extract_and_reject_changed_archive(self):
        archive=self.shared/'package.zip'
        with zipfile.ZipFile(archive,'w') as z:
            for p in self.package.rglob('*'):
                if p.is_file() and p.name!='station-provenance.json':z.write(p,'package/'+p.relative_to(self.package).as_posix())
        self.entry['archive_sha256']=desktop.digest(archive)
        root,package=station.unpack(self.shared,self.entry,self.root/'school')
        self.assertEqual(package['backend'],'vcs');desktop.verify(root)
        archive.write_bytes(b'changed')
        with self.assertRaises(ValueError):station.unpack(self.shared,self.entry,self.root/'school')

    def test_menu_exits_and_rejects_bulk_selection(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(station.choose(['one','two'],'case',read=lambda _: '0'))
            with self.assertRaises(ValueError):station.choose(['one','two'],'case',read=lambda _:'1,2')


if __name__=='__main__':unittest.main()
