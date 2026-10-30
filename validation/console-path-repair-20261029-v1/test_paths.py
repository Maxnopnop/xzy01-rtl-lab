"""Synthetic only. Never constructs a real release or dispatches a real package."""
import contextlib,io,json,os,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE/'source'))
import console_bridge_v3 as b
import console_paths as paths
from test_console_multimodel import fixture
OBSERVATIONS=[]
ORIGINAL_CHECK_RELEASE=b.Package.check_release

class PathTests(unittest.TestCase):
    def setUp(self):
        work=HERE/'t';work.mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=work);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.manifest=fixture(self.root/'p');self.pkg=b.Package(self.manifest,self.root/'w')
        self.key='FAKE_MEMORY_ONLY_SECRET_2947'
        self.adapter=SimpleNamespace(route_values=lambda c,e:dict(endpoint=c['endpoint'],proxy_url=None),send_once=Mock(side_effect=self.reply))
        self.local={'fixed_test':'FIXED_TEST_PASS','synthesis':'SYNTH_PASS','infrastructure_stop':False}
        for patcher in (patch.object(b.Package,'check_release',return_value=None),patch.object(b,'transport',return_value=self.adapter),patch.object(b,'local_replay',side_effect=lambda *a,**k:self.local)):
            patcher.start();self.addCleanup(patcher.stop)
    def reply(self,raw,*args):
        req=json.loads(raw);profile=self.pkg.models[req['model']]
        return dict(outcome='HTTP_OK',request_sha256=b.digest(raw),client_post_invocations=1,body=json.dumps(dict(model=req['model'],provider=profile['response_provider'],usage={'completion_tokens':1},choices=[dict(finish_reason='stop',message=dict(role='assistant',content='module TopModule(output x); assign x=0; endmodule'))])))
    def run_slot(self,slot='offline-1'):return self.pkg.dispatch(None,slot,self.key)
    def blocked(self,slot='offline-2',posts=1):
        with self.assertRaises(Exception):self.run_slot(slot)
        self.assertEqual(self.adapter.send_once.call_count,posts)
    def test_windows_original_depth_and_deeper_real_file_writes(self):
        self.assertEqual(os.name,'nt','This acceptance requires actual Windows')
        base=self.root/'long';base.mkdir()
        target_parent_length=239 # request=252, response=263: >= original incident
        folder=base/('x'*(target_parent_length-len(str(base))-1));folder.mkdir()
        obs=[]
        for name in ('request.json','reservation.json','transport-response.json','result.json'):
            p=folder/name
            try:b.save(p,{'synthetic':True});saved=True;error=None
            except OSError as exc:saved=False;error=paths.error_record(exc,'actual_windows_probe')
            obs.append(dict(name=name,path_length=len(str(p)),saved=saved,error=error))
        self.assertTrue(obs[0]['saved']);self.assertFalse(obs[2]['saved']);self.assertTrue(obs[3]['saved'])
        OBSERVATIONS.append(dict(case='actual_windows_path_depth',probe=obs,model_calls=0))
    def test_short_paths_all_actual_preflight_writes_and_normal_continue(self):
        original=paths.probe;seen=[]
        def probe(p):original(p);seen.append(str(p))
        with patch.object(paths,'probe',side_effect=probe):
            for i in range(1,7):self.assertEqual(self.run_slot('offline-'+str(i))['status'],'GENERATED_UNVERIFIED')
        self.assertEqual(self.adapter.send_once.call_count,6)
        self.assertTrue(any('/local/' in p.replace('\\','/') and p.endswith('netlist.json') for p in seen))
        self.assertTrue(any(p.endswith('transport-response.json') for p in seen))
        self.assertLess(max(map(len,seen)),240)
        for i,s in enumerate(self.pkg.slots):
            self.assertEqual(self.adapter.send_once.call_args_list[i].args[0],(self.manifest.parent/s['request']).read_bytes())
        OBSERVATIONS.append(dict(case='short_preflight',paths_probed=len(seen),max_length=max(map(len,seen)),mock_posts=6))
    def test_preflight_response_failure_zero_posts(self):self.preflight_failure('transport-response.json')
    def test_preflight_deeper_local_failure_zero_posts(self):self.preflight_failure('netlist.json')
    def preflight_failure(self,name):
        original=paths.probe
        def probe(p):
            if p.name==name:raise PermissionError(13,'synthetic denied '+self.key)
            original(p)
        with patch.object(paths,'probe',side_effect=probe):
            with self.assertRaises(b.DispatchFailure) as caught:self.run_slot()
        self.assertEqual(self.adapter.send_once.call_count,0)
        result=b.read(self.pkg.slot_dir('offline-1')/'result.json')
        self.assertEqual(result['stage'],'path_preflight');self.assertFalse(result['send_attempted']);self.assertEqual(result['status'],'UNKNOWN')
        self.assertTrue((self.pkg.state/'STOP.json').exists());self.blocked(posts=0)
        self.assertNotIn(self.key,json.dumps(caught.exception.diagnostic))
    def test_over_budget_work_path_no_posts(self):
        self.pkg=b.Package(self.manifest,self.root/('w'*85))
        with self.assertRaises(Exception):self.run_slot()
        self.assertEqual(self.adapter.send_once.call_count,0)
    def test_primary_response_save_failure_retains_fake_envelope(self):
        original=b.save
        def save(p,value):
            if p.name=='transport-response.json':raise FileNotFoundError(2,'synthetic '+self.key)
            original(p,value)
        with patch.object(b,'save',side_effect=save):
            with self.assertRaises(b.DispatchFailure) as caught:self.run_slot()
        r=b.read(self.pkg.slot_dir('offline-1')/'result.json');fallback=b.read(self.pkg.recovery_path(self.pkg.slots[0]))
        self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(r['stage'],'response_persist');self.assertEqual(r['recovery'],'SAVED')
        self.assertEqual(fallback['transport_response'],self.reply((self.manifest.parent/'request-1.json').read_bytes()))
        self.assertEqual(r['response_sha256'],b.digest(b.canonical(fallback['transport_response'])))
        self.assertEqual(caught.exception.diagnostic['errno'],2);self.blocked()
        OBSERVATIONS.append(dict(case='response_fallback',status=r['status'],stage=r['stage'],recovery=r['recovery'],mock_posts=1,recovered_synthetic_record=fallback))
    def test_double_response_failure_and_all_receipt_failures_no_resend(self):
        original=b.save
        def save(p,value):
            if p.name in ('transport-response.json','result.json','STOP.json') or p.parent.name=='e':raise OSError(28,'synthetic full '+self.key)
            original(p,value)
        with patch.object(b,'save',side_effect=save):
            with self.assertRaises(b.DispatchFailure) as caught:self.run_slot()
        d=caught.exception.diagnostic
        self.assertEqual(d['status'],'UNKNOWN');self.assertEqual(d['recovery'],'PERSIST_FAILED');self.assertEqual(len(d['storage_errors']),3)
        self.assertFalse((self.pkg.state/'STOP.json').exists());self.assertTrue(self.pkg.reservation_path('offline-1').exists())
        self.assertEqual(self.pkg.rows()[0]['status'],'UNKNOWN');self.blocked();self.blocked('offline-1')
        OBSERVATIONS.append(dict(case='all_storage_failures',diagnostic=d,mock_posts=1,remaining_response_evidence='UNRECOVERABLE: memory lost after exit'))
    def test_response_secret_echo_suppressed_on_all_paths(self):
        self.adapter.send_once.side_effect=lambda *a:dict(outcome='HTTP_OK',body=self.key)
        with self.assertRaises(b.DispatchFailure):self.run_slot()
        self.assertFalse(self.pkg.recovery_path(self.pkg.slots[0]).exists())
        for p in self.root.rglob('*'):
            if p.is_file():self.assertNotIn(self.key.encode(),p.read_bytes())
    def test_mapping_collision_missing_or_tampered_blocks(self):
        self.pkg.ensure_mapping();p=self.pkg.state/'identity.json';good=p.read_bytes()
        bad=b.read(p);bad['manifest_sha256']='0'*64;p.write_bytes(b.canonical(bad));self.blocked('offline-1',0)
        p.write_bytes(good);bad=b.read(p);bad['slots'][0]['id']='other';p.write_bytes(b.canonical(bad));self.blocked('offline-1',0)
        p.unlink();self.blocked('offline-1',0)
    def test_old_global_reservation_blocks_changed_manifest_and_other_slots(self):
        old=self.root/'legacy';p=old/'slot-reservations/offline-1.json';p.parent.mkdir(parents=True);p.write_bytes(b'{}');before=b.sha(p)
        data=b.read(self.manifest);data['name']='OTHER_PACKAGE';self.manifest.write_bytes(b.canonical(data));self.pkg=b.Package(self.manifest,self.root/'other')
        with patch.object(b,'LEGACY_STATES',(old,)):
            self.blocked('offline-1',0);self.blocked('offline-2',0)
            self.assertEqual(self.pkg.rows()[0]['status'],'UNKNOWN')
        self.assertEqual(b.sha(p),before)
    def test_old_dispatch_evidence_blocks_without_global_file(self):
        old=self.root/'legacy';(old/'dispatch'/self.pkg.identity).mkdir(parents=True)
        with patch.object(b,'LEGACY_STATES',(old,)):self.blocked('offline-1',0)
    def test_request_tamper_zero_posts(self):
        (self.manifest.parent/'request-1.json').write_bytes(b'{}');self.blocked('offline-1',0)
    def test_envelope_request_identity_drift_stops(self):
        def reply(*a):r=self.reply(*a);r['request_sha256']='wrong';return r
        self.adapter.send_once.side_effect=reply
        with self.assertRaises(b.DispatchFailure):self.run_slot()
        self.blocked()
    def test_no_actual_release_no_send(self):
        # Invoke the real check directly; no synthetic release file is ever created.
        with patch.object(b.Package,'check_release',ORIGINAL_CHECK_RELEASE):
            with self.assertRaises(b.DispatchFailure):self.run_slot()
        self.assertEqual(self.adapter.send_once.call_count,0)
    def test_http_error_no_stop_still_blocks(self):
        def reply(*a):r=self.reply(*a);r.update(outcome='HTTP_ERROR',body='synthetic error');return r
        self.adapter.send_once.side_effect=reply
        r=self.run_slot();self.assertEqual(r['status'],'HTTP_ERROR')
        (self.pkg.state/'STOP.json').unlink();self.blocked()
    def test_infrastructure_failure_no_stop_still_blocks(self):
        self.local['infrastructure_stop']=True;self.run_slot();(self.pkg.state/'STOP.json').unlink();self.blocked()
    def test_ordinary_function_compile_synthesis_failures_continue(self):
        self.local.update(fixed_test='COMPILE_ERROR',synthesis='SYNTH_FAIL');self.run_slot()
        self.local.update(fixed_test='FUNCTION_FAIL');self.run_slot('offline-2')
        self.assertEqual(self.adapter.send_once.call_count,2)
    def test_gui_thread_failure_refreshes_unknown_and_stop(self):
        import tkinter as tk
        import console_gui_v3 as gui
        root=tk.Tk();root.withdraw();self.addCleanup(root.destroy)
        app=gui.Console(root);app.package=self.pkg;app.display(self.pkg.rows())
        original=b.save
        def save(p,v):
            if p.name=='transport-response.json':raise OSError(2,'synthetic')
            original(p,v)
        with patch.object(b,'save',side_effect=save),patch.object(gui.messagebox,'showerror') as dialog:
            app.background(self.run_slot,lambda value:None)
            deadline=time.monotonic()+5
            while app.busy and time.monotonic()<deadline:root.update();time.sleep(.01)
        self.assertFalse(app.busy);self.assertEqual(app.rows[0]['status'],'UNKNOWN');self.assertTrue(app.rows[0]['stopped'])
        self.assertEqual(app.table.item('0')['values'][5],'UNKNOWN');self.assertIn('STOP',app.status.get());dialog.assert_called_once()
        self.assertEqual(self.adapter.send_once.call_count,1)

if __name__=='__main__':unittest.main()
