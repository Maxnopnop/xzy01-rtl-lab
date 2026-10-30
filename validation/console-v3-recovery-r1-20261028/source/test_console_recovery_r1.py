"""Recovery regression; synthetic POST/EDA only, all ledgers in TemporaryDirectory."""
import contextlib
import io
import json
from pathlib import Path
import shlex
import unittest
from unittest.mock import patch
import console_bridge_v3 as b
import console_school_runner_v3 as runner
import console_stage_v3 as stage
import test_console_multimodel as fixtures

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.case=fixtures.ModelTests('test_no_release_or_fixture_can_execute');self.case.setUp()
        self.addCleanup(self.case.doCleanups)
    def stop_crash(self,kind):
        c=self.case;original=b.save
        def save(path,value):
            if Path(path).name=='STOP.json':raise SystemExit('crash-before-STOP')
            original(path,value)
        local={'fixed_test':'FIXED_TEST_PASS','synthesis':'SYNTH_PASS','infrastructure_stop':False}
        if kind=='infrastructure':local.update(infrastructure_stop=True)
        elif kind in ('HTTP_ERROR','UNKNOWN','REDIRECT_REJECTED'):
            c.adapter.send_once.side_effect=None;c.adapter.send_once.return_value={'outcome':kind}
        elif kind=='identity':
            def bad_reply(*args):
                r=c.reply(*args);body=json.loads(r['body']);body['model']='wrong/model';r['body']=json.dumps(body);return r
            c.adapter.send_once.side_effect=bad_reply
        elif kind=='protocol':c.adapter.send_once.side_effect=None;c.adapter.send_once.return_value={'outcome':'HTTP_OK','body':'{bad-json'}
        elif kind=='extraction':local=None
        with patch.object(b,'save',side_effect=save),patch.object(b,'transport',return_value=c.adapter),patch.object(b,'local_replay',side_effect=ValueError('synthetic') if local is None else None,return_value=local):
            with self.assertRaises(SystemExit):c.pkg.dispatch(c.release,'offline-1','synthetic-secret')
        self.assertFalse((c.pkg.state/'STOP.json').exists())
        self.assertTrue((c.pkg.state/'offline-1/result.json').exists())
        self.assert_blocked()
    def assert_blocked(self):
        c=self.case
        with self.assertRaises(ValueError):c.pkg.gate(c.release,'offline-2')
        with self.assertRaises(ValueError):c.dispatch('offline-2')
        with self.assertRaises(ValueError):c.dispatch('offline-1')
        self.assertEqual(c.adapter.send_once.call_count,1)
    def test_crash_http_error(self):self.stop_crash('HTTP_ERROR')
    def test_crash_unknown(self):self.stop_crash('UNKNOWN')
    def test_crash_redirect(self):self.stop_crash('REDIRECT_REJECTED')
    def test_crash_infrastructure(self):self.stop_crash('infrastructure')
    def test_crash_identity(self):self.stop_crash('identity')
    def test_crash_protocol(self):self.stop_crash('protocol')
    def test_crash_extraction(self):self.stop_crash('extraction')
    def test_missing_corrupt_unknown_or_incomplete_result(self):
        c=self.case;c.dispatch();p=c.pkg.state/'offline-1/result.json';good=b.read(p)
        cases=[None,b'{broken',b'null',b'[]',b'{}']
        for key in ('schema','status','local','request_sha256','rtl_sha256','requested_model','response_model','reported_provider'):
            obj=dict(good);del obj[key];cases.append(b.canonical(obj))
        for field,value in [('schema','future-schema'),('status','FUTURE_STATUS'),('local',[]),('local',None)]:
            cases.append(b.canonical(dict(good,**{field:value})))
        for field,value in [('fixed_test','UNKNOWN'),('synthesis','NOT_RUN'),('synthesis','ENVIRONMENT_ERROR'),('infrastructure_stop',0),('infrastructure_stop','false'),('infrastructure_stop',True)]:
            cases.append(b.canonical(dict(good,local=dict(good['local'],**{field:value}))))
        for key in ('fixed_test','synthesis','infrastructure_stop'):
            loc=dict(good['local']);del loc[key];cases.append(b.canonical(dict(good,local=loc)))
        for raw in cases:
            with self.subTest(raw=raw):
                if raw is None:p.unlink(missing_ok=True)
                else:p.write_bytes(raw)
                self.assert_blocked()
        self.assertFalse((c.pkg.state/'STOP.json').exists())
    def test_legitimate_function_compile_synthesis_failures_continue(self):
        c=self.case;c.dispatch();p=c.pkg.state/'offline-1/result.json';good=b.read(p)
        for fixed in ('FIXED_TEST_PASS','FUNCTION_FAIL','COMPILE_ERROR','CHECK_COUNT_DIFFERENT'):
            for synth in ('SYNTH_PASS','SYNTH_FAIL'):
                with self.subTest(fixed=fixed,synth=synth):
                    p.write_bytes(b.canonical(dict(good,local={'fixed_test':fixed,'synthesis':synth,'infrastructure_stop':False})))
                    self.assertEqual(c.pkg.gate(c.release,'offline-2')['id'],'offline-2')
        c.dispatch('offline-2');self.assertEqual(c.adapter.send_once.call_count,2)

class ShipHintTests(unittest.TestCase):
    def test_copyable_quoted_hint_and_ship_branch_without_eda(self):
        c=fixtures.SchoolTests('test_old_history_read_only_and_counts');c.setUp();self.addCleanup(c.doCleanups)
        record=c.package('vcs');dest=stage.stage(c.share/record['archive'],record['archive_sha256'],c.home)
        share=c.home/"share with space and 'quote'";share.mkdir()
        output=io.StringIO()
        with patch.object(runner,'__file__',str(dest/'console_school_runner_v3.py')),patch.object(runner.Path,'home',return_value=c.home),patch.object(runner,'school_host',return_value=True),patch.object(runner,'execute',return_value={'status':'ENVIRONMENT_ERROR','returncode':None}) as execute,patch.object(runner.sys,'argv',['runner','run',str(share)]):
            with patch.object(runner,'ship',side_effect=OSError('synthetic share unavailable')),contextlib.redirect_stdout(output):runner.main()
            line=next(x for x in output.getvalue().splitlines() if x.startswith('Return retained;'))
            argv=shlex.split(line.split('retry transfer only: ',1)[1])
            self.assertEqual(argv,['python3',str(dest/'console_school_runner_v3.py'),'ship',str(share.resolve())])
            with patch.object(runner.sys,'argv',argv[1:]):self.assertEqual(runner.main(),0)
            self.assertEqual(execute.call_count,1)
            self.assertTrue((share/('return-'+record['key']+'.json')).exists())

if __name__=='__main__':unittest.main()
