"""Offline acceptance only. Synthetic replies are never model evidence."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile
import console_bridge as b
import console_school as school

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.base=self.root/'packet';self.base.mkdir()
        for n in ('spec.txt','tb.sv','ref.sv'):(self.base/n).write_bytes(b'original\r\n')
        self.messages=[{'role':'system','content':'RTL only\r\n'},{'role':'user','content':'  中文原文\r\n\t保留  '}]
        slots=[]
        for i,model in enumerate(b.MODELS*2):
            req=dict(model=model,messages=self.messages,stream=False,provider={'only':['openai'],'allow_fallbacks':False,'require_parameters':True})
            p=self.base/f'{i}.json';p.write_bytes(json.dumps(req,ensure_ascii=False,indent=2).encode())
            slots.append(dict(id=f'fixture-{i}',ordinal=i+1,sample=1,task='fixture',condition='no_rag' if i<3 else 'rag',model=model,request=p.name,testbench='tb.sv',reference='ref.sv',spec='spec.txt',expected_checks=213,top='TopModule'))
        self.manifest=dict(schema='console-frozen-v1',name='OFFLINE_FIXTURE',budget_policy='calls_only',max_calls=6,slots=slots,files={p.name:b.sha(p) for p in self.base.iterdir()})
        self.path=self.base/'console-package.json';self.path.write_bytes(b.canonical(self.manifest))
        self.pkg=b.Package(self.path,self.root/'state')
        self.release=self.root/'release.json'
        self.approve()
    def approve(self):
        self.release.write_bytes(b.canonical(dict(decision='CONSOLE_EXECUTION_RELEASE',user_approved=True,owner='exploration',reviewer_thread_id='01a12088-049c-7f32-8167-48be03bcc145',manifest_sha256=self.pkg.identity,bridge_sha256=b.sha(b.__file__),transport_sha256=b.TRANSPORT_SHA,max_calls=6,budget_policy='calls_only',permitted_slots=[s['id'] for s in self.pkg.slots],automatic_retries=0,request_timeout_seconds=180)))
        r=b.read(self.release);r['source_hashes']=b.bridge_bindings();self.release.write_bytes(b.canonical(r))
    def reply(self,raw,route,secret,timeout):
        self.assertEqual(raw,(self.base/'0.json').read_bytes())
        self.assertEqual(route['endpoint'],b.ENDPOINT)
        self.assertEqual(timeout,180)
        return dict(outcome='HTTP_OK',request_sha256=b.digest(raw),client_post_invocations=1,body=json.dumps(dict(model=b.MODELS[0],provider='OpenAI',choices=[dict(finish_reason='stop',message=dict(role='assistant',content='module TopModule(output x); assign x=0; endmodule'))],usage={'prompt_tokens':10,'completion_tokens':11})))
    def test_import_preview_no_auth_and_missing_budget_preserved(self):
        with patch.object(b,'transport',side_effect=AssertionError('no network')):
            rows=self.pkg.rows();self.assertEqual(len(rows),6)
            self.assertEqual(len({r['messages_actual_sha256'] for r in rows}),1)
            self.assertTrue(all(r['output_budget'] is None for r in rows))
        self.assertEqual(self.messages,json.loads((self.base/'0.json').read_bytes())['messages'])
    def test_skip_order_and_unbalanced_arms_refused(self):
        with self.assertRaises(ValueError):self.pkg.gate(self.release,'fixture-1')
        self.manifest['slots']=self.manifest['slots'][:3];self.manifest['max_calls']=3
        self.path.write_bytes(b.canonical(self.manifest))
        with self.assertRaises(ValueError):b.Package(self.path,self.root/'state')
    def test_local_infrastructure_stops_but_function_fail_preserved(self):
        adapter=b.transport();adapter.send_once=self.reply
        with patch.object(b,'transport',return_value=adapter),patch.object(b,'local_replay',return_value={'fixed_test':'FUNCTION_FAIL','synthesis':'SYNTH_PASS','infrastructure_stop':False}):
            r=self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
        self.assertEqual(r['local']['fixed_test'],'FUNCTION_FAIL');self.assertFalse((self.pkg.state/'STOP.json').exists())
        self.assertEqual(self.pkg.gate(self.release,'fixture-1')['id'],'fixture-1')
    def test_infrastructure_stop_gate(self):
        adapter=b.transport();adapter.send_once=self.reply
        with patch.object(b,'transport',return_value=adapter),patch.object(b,'local_replay',return_value={'fixed_test':'INFRASTRUCTURE_ERROR','synthesis':'NOT_RUN','infrastructure_stop':True}):
            self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
        with self.assertRaises(ValueError):self.pkg.gate(self.release,'fixture-1')
    def test_no_release_blocks_before_reservation(self):
        self.release.unlink()
        with patch.object(b,'transport',side_effect=AssertionError('no network')):
            with self.assertRaises(ValueError):self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
        self.assertFalse((self.pkg.state/'fixture-0').exists())
    def test_exact_bytes_secret_hidden_single_post_no_repeat(self):
        adapter=b.transport();adapter.send_once=unittest.mock.Mock(side_effect=self.reply)
        secret='synthetic-secret'
        before={p.name:b.sha(p) for p in self.base.iterdir()}
        with patch.object(b,'transport',return_value=adapter),patch.object(b,'local_replay',return_value={'fixed_test':'FIXED_TEST_PASS','synthesis':'SYNTH_PASS'}) as local:
            result=self.pkg.dispatch(self.release,'fixture-0',secret)
            self.assertEqual(adapter.send_once.call_count,1);self.assertEqual(local.call_count,1)
            self.assertEqual(result['usage']['prompt_tokens'],10);self.assertIsNone(result['cost'])
            with self.assertRaises(ValueError):self.pkg.dispatch(self.release,'fixture-0',secret)
            self.assertEqual(adapter.send_once.call_count,1)
        for p in (self.root/'state').rglob('*'):
            if p.is_file():self.assertNotIn(secret.encode(),p.read_bytes())
        self.assertEqual(before,{p.name:b.sha(p) for p in self.base.iterdir()})
    def test_unknown_and_failure_stop_no_retries(self):
        adapter=b.transport();adapter.send_once=unittest.mock.Mock(return_value={'outcome':'UNKNOWN','client_post_invocations':1})
        with patch.object(b,'transport',return_value=adapter):
            result=self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
            self.assertEqual(result['status'],'UNKNOWN')
            for slot in ('fixture-0','fixture-1'):
                with self.assertRaises(ValueError):self.pkg.dispatch(self.release,slot,'synthetic-secret')
            self.assertEqual(adapter.send_once.call_count,1)
    def test_request_drift_and_cross_model_difference(self):
        (self.base/'1.json').write_bytes(b'{}')
        with self.assertRaises(ValueError):self.pkg.verify()
        obj=json.loads((self.base/'0.json').read_bytes());obj['model']=b.MODELS[1];obj['messages'][1]['content']='changed'
        (self.base/'1.json').write_bytes(b.canonical(obj));self.manifest['files']['1.json']=b.sha(self.base/'1.json')
        self.path.write_bytes(b.canonical(self.manifest))
        with self.assertRaises(ValueError):b.Package(self.path,self.root/'state')
    def test_budget_release_mismatch_and_exclusive_lock(self):
        r=b.read(self.release);r['max_calls']=4;self.release.write_bytes(b.canonical(r))
        with self.assertRaises(ValueError):self.pkg.gate(self.release,'fixture-0')
        self.approve();self.pkg.state.mkdir(parents=True)
        (self.pkg.state/'exclusive.lock').write_text('occupied')
        with self.assertRaises(FileExistsError):self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
    def test_historical_slot_refused(self):
        fake=self.root/'fake';p=fake/'e/runtime/live-run/reservations';p.mkdir(parents=True)
        (p/'fixture-0.json').write_text('{}')
        with patch.object(b,'HISTORY',{'existing':('batch',str(fake/'e'))}):
            with self.assertRaises(ValueError):self.pkg.gate(self.release,'fixture-0')
    def test_hidden_key_launcher_is_bound_no_secret(self):
        from console_cli import export_launcher
        output=self.root/'Start-One.ps1'
        export_launcher(self.path,self.release,output)
        text=output.read_text();self.assertIn(self.pkg.identity,text);self.assertIn(b.sha(self.release),text)
        self.assertNotIn('synthetic-secret',text);self.assertIn('run-next',text)
    def test_real_loopback_transport_auth_redirect_and_no_retry(self):
        seen=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append((self.headers.get('Authorization'),self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(302);self.send_header('Location','https://example.invalid');self.end_headers();self.wfile.write(b'redirect')
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            raw=(self.base/'0.json').read_bytes()
            env=b.transport().send_once(raw,{'endpoint':f'http://127.0.0.1:{server.server_port}/chat/completions','proxy_url':None},'synthetic-secret',5)
            self.assertEqual(env['outcome'],'REDIRECT_REJECTED');self.assertEqual(len(seen),1)
            self.assertEqual(seen[0],('Bearer synthetic-secret',raw));self.assertNotIn('synthetic-secret',json.dumps(env))
        finally:server.shutdown();server.server_close();thread.join()
    def test_secret_echo_never_persisted(self):
        adapter=b.transport();adapter.send_once=lambda *args:dict(outcome='HTTP_ERROR',body='synthetic-secret')
        with patch.object(b,'transport',return_value=adapter):
            with self.assertRaises(ValueError):self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
        for p in (self.root/'state').rglob('*'):
            if p.is_file():self.assertNotIn(b'synthetic-secret',p.read_bytes())
    def test_model_identity_failure_retains_usage(self):
        def reply(*args):
            r=self.reply(*args);body=json.loads(r['body']);body['model']='different';body['usage']['cost']=.01;r['body']=json.dumps(body);return r
        adapter=b.transport();adapter.send_once=reply
        with patch.object(b,'transport',return_value=adapter):result=self.pkg.dispatch(self.release,'fixture-0','synthetic-secret')
        self.assertEqual(result['status'],'MODEL_OR_PROVIDER_MISMATCH');self.assertEqual(result['cost'],.01)

class SchoolTests(unittest.TestCase):
    def test_saved_rtl_test_and_reference_tampering_rejected(self):
        import shutil
        row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'STATE',Path(tmp)/'state'):
            cloned=Path(tmp)/'job';shutil.copytree(row['job_dir'],cloned)
            row=dict(row,job_dir=str(cloned))
            shared=Path(tmp)/'share';shared.mkdir()
            for name in ('dut.sv','testbench.sv','reference.sv'):
                p=cloned/name;original=p.read_bytes();p.write_bytes(original+b'\n// replaced input\n')
                with self.assertRaises(ValueError):school.pack(row,'vcs',shared)
                p.write_bytes(original)
            self.assertEqual(list(shared.iterdir()),[])
    def test_assets_export_rejected_explicitly(self):
        row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'assets'):
                school.pack(dict(row,assets=['vectors.hex']),'xcelium',Path(tmp))
    def test_four_tools_and_recovery_scripts_generate_offline(self):
        import ast
        row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'STATE',Path(tmp)/'state'):
            shared=Path(tmp)/'share';shared.mkdir();sdc=Path(tmp)/'fixture.sdc';sdc.write_text('set_max_delay 10 -from [all_inputs] -to [all_outputs]\n')
            for tool in ('vcs','xcelium','dc','genus'):
                profile=dict(libraries=['/synthetic/library.'+('db' if tool=='dc' else 'lib')],corner='fixture',constraints_reviewed=True,timeout_seconds=600)
                record=school.pack(row,tool,shared,profile,sdc)
                folder=Path(record['shared'])
                for name in ('run-one.sh','check-share.sh','ship-only.sh'):self.assertTrue((folder/name).exists())
                self.assertIn('ship-only.sh',school.command(record,'ship'))
                self.assertNotIn('exec python3', (folder/'check-share.sh').read_text())
                ast.parse((folder/'console_school_runner.py').read_text(),feature_version=(3,6))
    def test_school_failure_collects_without_rerun_and_ship_only(self):
        import console_school_runner as runner
        row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'STATE',Path(tmp)/'state'):
            shared=Path(tmp)/'share';shared.mkdir();home=Path(tmp)/'home';home.mkdir()
            record=school.pack(row,'vcs',shared)
            with patch.object(runner,'__file__',str(Path(record['shared'])/'console_school_runner.py')),patch.object(runner,'school_host',return_value=True),patch.object(runner.Path,'home',return_value=home),patch.object(runner,'execute',side_effect=OSError('synthetic tool absent')) as execute,patch.object(runner.sys,'argv',['runner']):
                self.assertEqual(runner.main(),1);self.assertEqual(execute.call_count,1)
                side=Path(record['shared'])/'inbox'/record['key']/'console-return.json'
                self.assertEqual(school.collect(record,side)['status'],'ENVIRONMENT_ERROR')
                with patch.object(runner.sys,'argv',['runner','ship']):self.assertEqual(runner.main(),0)
                self.assertEqual(execute.call_count,1)
                with self.assertRaises(FileExistsError):runner.main()
    def test_history_counts_never_upgraded(self):
        rows=b.school_history();self.assertTrue(rows)
        differing=[r for r in rows if r.get('samples') in (211,212)]
        self.assertTrue(differing);self.assertTrue(all(r['status']=='CHECK_COUNT_DIFFERENT' for r in differing))
    def test_package_missing_share_tamper_return_and_count(self):
        row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        before=b.sha(Path(row['job_dir'])/'dut.sv')
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'STATE',Path(tmp)/'state'):
            shared=Path(tmp)/'share';shared.mkdir()
            record=school.pack(row,'vcs',shared)
            self.assertIn(record['key'],school.command(record))
            folder=Path(record['local']);manifest=b.read(folder/'console-manifest.json')
            result=dict(key=record['key'],manifest_sha256=record['manifest_sha256'],status='CHECK_COUNT_DIFFERENT',returncode=0,samples=212)
            returned=Path(tmp)/'return';returned.mkdir();archive=returned/'console-return.zip'
            with zipfile.ZipFile(archive,'w') as z:
                for name in list(manifest['inputs'])+['console-manifest.json']:z.write(folder/name,name)
                z.writestr('console-result.json',b.canonical(result));z.writestr('simulate.log','Mismatches: 0 in 212 samples\n');z.writestr('simulate.exit','0')
            b.save(returned/'console-return.json',dict(key=record['key'],manifest_sha256=record['manifest_sha256'],archive_sha256=b.sha(archive)))
            imported=school.collect(record,returned/'console-return.json');self.assertEqual(imported['status'],'CHECK_COUNT_DIFFERENT')
            self.assertEqual(imported,school.collect(record,returned/'console-return.json'))
            (Path(record['shared'])/'run-one.sh').unlink()
            with self.assertRaises(FileNotFoundError):school.command(record)
            with archive.open('ab') as f:f.write(b'tamper')
            with self.assertRaises(ValueError):school.collect(record,returned/'console-return.json')
        self.assertEqual(before,b.sha(Path(row['job_dir'])/'dut.sv'))
    def test_synthesis_pack_contains_no_library(self):
        row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'STATE',Path(tmp)/'state'):
            shared=Path(tmp)/'share';shared.mkdir();sdc=Path(tmp)/'fixture.sdc';sdc.write_text('set_max_delay 10 -from [all_inputs] -to [all_outputs]\n')
            profile=dict(libraries=['/synthetic/library.db'],corner='fixture',constraints_reviewed=True,timeout_seconds=600)
            record=school.pack(row,'dc',shared,profile,sdc)
            self.assertFalse(any(p.suffix in ('.db','.lib') for p in Path(record['shared']).iterdir()))
            self.assertIn('run-one.sh',record['files'])

class GuiTests(unittest.TestCase):
    def test_hidden_native_window_reads_336_and_no_network(self):
        import tkinter as tk
        from console_gui_v2 import Console
        root=tk.Tk();root.withdraw()
        try:
            with patch.object(b,'transport',side_effect=AssertionError('no network')):
                app=Console(root);root.update();self.assertEqual(len(app.rows),336)
                app.load_history('new96');self.assertEqual(len(app.rows),96)
                app.table.selection_set('24');app.details()
                self.assertIn('Prob094',app.detail.get('1.0','end'))
                app.key.set('synthetic-key');self.assertEqual(app.redact('synthetic-key'),'[REDACTED]')
        finally:root.destroy()

if __name__=='__main__':unittest.main()
