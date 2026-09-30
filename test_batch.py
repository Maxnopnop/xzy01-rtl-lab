"""Integration tests execute real Icarus. Bridge fixtures are synthetic, not VCS evidence."""
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import batch
import rtl_lab as lab
import school_bridge as bridge


class BatchTests(unittest.TestCase):
    def setUp(self):
        base=lab.ROOT/'test-results';base.mkdir(exist_ok=True)
        self.folder=Path(tempfile.mkdtemp(prefix='batch_',dir=base))

    def call(self,*args):
        result=lab.run_process([sys.executable,str(lab.ROOT/'batch.py'),*map(str,args)],lab.ROOT,60)
        self.assertFalse(result['timeout'],result)
        self.assertNotIn('Traceback',result['stderr'])
        return result

    def init(self,folder,mode='offline',tasks='adder8,encoder4,counter4',samples=2,*extra):
        result=self.call('init','--run-dir',folder,'--mode',mode,'--tasks',tasks,'--samples',samples,*extra)
        self.assertEqual(result['returncode'],0,result['stderr'])

    def test_parallel_resume_and_no_duplicate(self):
        run=self.folder/'resume';self.init(run)
        self.call('run','--run-dir',run,'--workers',2,'--max-jobs',2)
        self.assertEqual(batch.read(run/'summary.json')['completed'],2)
        before={p:lab.digest(p.read_bytes()) for p in run.glob('jobs/*/result.json')}
        self.assertEqual(self.call('run','--run-dir',run,'--workers',3)['returncode'],0)
        summary=batch.read(run/'summary.json')
        self.assertEqual(summary['counts'],{'PASS':6})
        for path,sha in before.items():self.assertEqual(lab.digest(path.read_bytes()),sha)
        self.assertEqual(self.call('run','--run-dir',run)['returncode'],0)
        self.assertEqual(len(list(run.glob('jobs/*/attempt_*'))),6)

    def test_lock_and_input_change(self):
        fixtures=self.folder/'fixtures';fixtures.mkdir()
        shutil.copyfile(lab.ROOT/'examples/correct/adder8.sv',fixtures/'adder8.sv')
        run=self.folder/'locked';self.init(run,'offline','adder8',1,'--rtl-dir',str(fixtures))
        with batch.lock(run):
            self.assertEqual(self.call('run','--run-dir',run)['returncode'],2)
        with (fixtures/'adder8.sv').open('a') as f:f.write('// changed\n')
        self.assertEqual(self.call('run','--run-dir',run)['returncode'],2)
        self.assertEqual(batch.read(run/'summary.json')['completed'],0)

    def test_manual_bridge_receipt_source_and_license(self):
        run=self.folder/'run';self.init(run,'offline','adder8',1)
        self.assertEqual(self.call('run','--run-dir',run)['returncode'],0)
        out=self.folder/'manual'
        with contextlib.redirect_stdout(io.StringIO()):bridge.export(run,out,'vcs','adder8__s001')
        case=out/'adder8__s001';meta=batch.read(case/'case.json')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bridge.import_results(out,out)[0]['status'],'NOT_RUN')
            # Explicit test-only synthetic commercial evidence; never a real VCS claim.
            (case/'tool_version.log').write_text('SYNTHETIC_TEST_NOT_VCS')
            (case/'compile.log').write_text('SYNTHETIC_TEST')
            (case/'simulate.log').write_text('SYNTHETIC_TEST')
            (case/'compile.exit').write_text('0')
            (case/'simulate.exit').write_text('0')
            (case/'verdict.txt').write_text(f'RTL_LAB_V1 {meta["nonce"]} checks={meta["checks"]} errors=0\n')
            self.assertEqual(bridge.import_results(out,out)[0]['status'],'PASS')
            (case/'verdict.txt').write_text('RTL_LAB_V1 stale checks=65536 errors=0\n')
            self.assertEqual(bridge.import_results(out,out)[0]['status'],'SIM_ERROR')
            (case/'simulate.log').write_text('Unable to checkout license')
            self.assertEqual(bridge.import_results(out,out)[0]['status'],'ENV_ERROR')
            (case/'dut.sv').write_text('changed')
            self.assertEqual(bridge.import_results(out,out)[0]['status'],'EVIDENCE_ERROR')

    def test_interrupt_persists_and_releases_lock(self):
        run=self.folder/'interrupt'
        self.init(run,'offline','adder8',1,'--rtl-dir',str(lab.ROOT/'examples/timeout'),'--sim-timeout','30')
        with (self.folder/'interrupt.log').open('wb') as log:
            proc=subprocess.Popen([sys.executable,str(lab.ROOT/'batch.py'),'run','--run-dir',str(run),'--workers','1'],stdout=log,stderr=log)
            deadline=time.monotonic()+10
            while not list(run.glob('jobs/*/attempt_*/001_*/compile.json')) and time.monotonic()<deadline:time.sleep(.05)
            if sys.platform=='win32':
                # SIGTERM is forceful on Windows: verifies crash restart and OS lock release.
                # Clean the whole job tree first, as a user would stopping the terminal process.
                lab.kill_tree(proc)
            else:
                proc.send_signal(signal.SIGINT);proc.wait(timeout=10)
        with batch.lock(run):pass
        result=self.call('run','--run-dir',run,'--workers',1)
        self.assertEqual(result['returncode'],1)
        self.assertEqual(batch.read(run/'summary.json')['counts'],{'TIMEOUT':1})
        self.assertEqual(len(list(run.glob('jobs/*/attempt_*'))),2)

    def test_plan_source_change_rejected(self):
        run=self.folder/'source';self.init(run)
        plan=batch.read(run/'plan.json');plan['source_hashes']['batch.py']='invalid';batch.atomic(run/'plan.json',plan)
        self.assertEqual(self.call('run','--run-dir',run)['returncode'],2)

    def test_call_cap_with_explicit_mock_http_not_real_llm(self):
        counter=[]
        source=(lab.ROOT/'examples/correct/adder8.sv').read_text(encoding='utf-8')
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                counter.append(1)
                body=json.dumps({'model':'MOCK_NOT_REAL_LLM','choices':[{'message':{'content':source},'finish_reason':'stop'}]}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            run=self.folder/'MOCK_HTTP_NOT_REAL_LLM'
            self.init(run,'live','adder8',3,'--base-url',f'http://127.0.0.1:{server.server_port}/v1',
                '--model','MOCK_NOT_REAL_LLM','--allow-anonymous','--max-calls','1','--api-key-env','UNUSED_MOCK_KEY')
            self.assertEqual(self.call('run','--run-dir',run,'--workers',3)['returncode'],1)
            self.assertEqual(len(counter),1)
            self.assertEqual(batch.read(run/'summary.json')['pending'],2)
            self.assertEqual(self.call('run','--run-dir',run,'--workers',3,'--max-calls',3)['returncode'],0)
            self.assertEqual(len(counter),3)
            self.assertEqual(batch.read(run/'summary.json')['model_call_reservations'],3)
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main(verbosity=2)
