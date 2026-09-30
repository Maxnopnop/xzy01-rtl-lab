"""Public-source development audit and real synthesis regression tests."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest

import batch
import build_dev
import pilot
import rtl_lab as lab
import synthesis


class DevelopmentTests(unittest.TestCase):
    def setUp(self):
        base=batch.ROOT/'test-results';base.mkdir(exist_ok=True)
        self.root=Path(tempfile.mkdtemp(prefix='dev_',dir=base))

    def test_sources_split_and_deterministic_rebuild(self):
        specs=batch.manifest('dev10')
        self.assertEqual(len(specs),10)
        self.assertEqual(sum(s['benchmark']=='RTLLM' for s in specs),5)
        original=build_dev.ROOT
        clone=self.root/'clone';shutil.copytree(original/'upstream',clone/'upstream')
        try:
            build_dev.ROOT=clone
            with contextlib.redirect_stdout(io.StringIO()):build_dev.build()
        finally:build_dev.ROOT=original
        for path in clone.rglob('*'):
            if path.is_file():self.assertEqual(path.read_bytes(),(original/path.relative_to(clone)).read_bytes(),str(path))

    def test_wildcard_allowed_but_attributes_rejected(self):
        for wildcard in ('@(*)','@ ( * )','@*'):
            code='module d(input a, output reg q); always '+wildcard+' q=a; endmodule'
            self.assertEqual(lab.extract_rtl(code,'d').strip(),code)
        with self.assertRaises(lab.LabError):lab.extract_rtl('module d(input a,output q); (* keep=1 *) wire b=a; assign q=b; endmodule','d')

    def test_reference_and_mutants(self):
        # Both suites use real Icarus; Yosys runs when available (required in CI).
        for fixture,status in [('reference','PASS'),('mutants','FUNCTION_FAIL')]:
            run=self.root/fixture
            args=['init','--run-dir',str(run),'--suite','dev10','--rtl-dir',str(build_dev.ROOT/fixture)]
            if shutil.which('yosys'):args+=['--synthesis','yosys']
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(batch.main(args),0)
                result=batch.main(['run','--run-dir',str(run),'--workers','4'])
            summary=batch.read(run/'summary.json')
            self.assertEqual(summary['counts'],{status:10})
            self.assertEqual(result,0 if status=='PASS' else 1)
            if shutil.which('yosys'):self.assertEqual(summary['synthesis_counts'],{'SYNTH_PASS':10})

    def test_bootstrap_keeps_pairs_and_benchmarks(self):
        specs=[dict(id='a',benchmark='A'),dict(id='b',benchmark='A'),dict(id='c',benchmark='B'),dict(id='d',benchmark='B')]
        first=dict(a=0,b=1/3,c=2/3,d=1)
        result=pilot.bootstrap([first,first],specs,replicates=200)
        self.assertEqual(result['model_intervals'][0],result['model_intervals'][1])
        self.assertEqual(result['model_2_minus_model_1_interval'],[0,0])
        self.assertEqual(result,pilot.bootstrap([first,first],specs,replicates=200))

    def test_pilot_plan_no_calls_and_settings_guard(self):
        root=self.root/'pilot'
        with contextlib.redirect_stdout(io.StringIO()):
            pilot.init(root,batch.ROOT/'experiments/pilot60.json')
        summary=batch.read(root/'pilot-summary.json')
        self.assertEqual(summary['planned'],60)
        self.assertEqual(summary['completed'],0)
        self.assertEqual(summary['statistics'],{})
        self.assertEqual([m['model_call_reservations'] for m in summary['models']],[0,0])
        other=root/'model_02/plan.json';plan=batch.read(other)
        plan['config']['temperature']=.7;batch.atomic(other,plan)
        with self.assertRaises(ValueError):pilot.report(root)

    @unittest.skipUnless(shutil.which('yosys'),'Native Yosys required; execute this test in WSL/Linux')
    def test_synthesis_faults_and_timeout(self):
        tool=synthesis.inspect(SimpleNamespace(yosys=None),self.root)
        cases=[('syntax','module bad( INVALID; endmodule', 'SYNTH_FAIL',10),
               ('drivers','module bad(input clk,a,b, output reg q); always @(posedge clk) q<=a; always @(posedge clk) q<=b; endmodule','SYNTH_FAIL',10),
               ('unsupported','module bad(input clk,a,d,output reg q); always @(posedge clk or posedge a) q<=d; endmodule','SYNTH_FAIL',10),
               ('timeout','module bad(input [999:0] a,output [1999:0] q); assign q=a*a; endmodule','SYNTH_TIMEOUT',.001)]
        for name,code,expected,limit in cases:
            folder=self.root/name;folder.mkdir();(folder/'dut.sv').write_text(code)
            self.assertEqual(synthesis.evaluate(folder,dict(module='bad'),tool,limit)['status'],expected,name)

    @unittest.skipUnless(shutil.which('yosys'),'Native Yosys required; execute this test in WSL/Linux')
    def test_replay_binding_resume_and_tamper(self):
        run=self.root/'replay'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(batch.main(['init','--run-dir',str(run),'--tasks','counter4']),0)
            self.assertEqual(batch.main(['run','--run-dir',str(run)]),0)
            original=(run/'jobs/counter4__s001/result.json').read_bytes()
            a=synthesis.review(run);b=synthesis.review(run)
        self.assertEqual(a,b);self.assertEqual(a['joint_passes'],1)
        self.assertEqual(original,(run/'jobs/counter4__s001/result.json').read_bytes())
        source=next(run.glob('jobs/*/attempt_*/001_*/dut.sv'))
        source.write_text('module counter4; endmodule')
        # Replayed results must not be reusable after RTL tampering.
        with self.assertRaises(ValueError):synthesis.review(run)


if __name__=='__main__':unittest.main()
