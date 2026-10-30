"""Offline v3 acceptance. All inference and school execution are synthetic mocks."""
import ast
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import zipfile
import console_bridge_v3 as b
import console_school_v3 as school
import console_stage_v3 as stage
import console_school_runner_v3 as runner

def fixture(root,count=3,samples=1,actual_metadata=False):
    root=Path(root);root.mkdir(parents=True)
    for n in ('spec.txt','tb.sv','ref.sv'):(root/n).write_bytes(b'OFFLINE ORIGINAL\r\n')
    models=[]
    seeds=[('openai/gpt-4.1-mini','openai','OpenAI','openai'),('anthropic/claude-sonnet-4.5','anthropic','Anthropic','anthropic-4.5'),('deepseek/deepseek-chat-v3.1','deepinfra/fp4','DeepInfra','deepseek')]
    for i in range(count):
        mid,tag,provider,cat=seeds[i] if i<3 else ('fixture/model-'+str(i),'upstream-'+str(i),'Provider '+str(i),None)
        mn=f'metadata-{i}.json';sn=f'source-{i}.json'
        if actual_metadata:
            source=b.STATE/'catalogue'/cat
            (root/mn).write_bytes((source/'response.json').read_bytes());(root/sn).write_bytes((source/'source.json').read_bytes())
        else:
            b.save(root/mn,{'data':{'id':mid,'endpoints':[dict(tag=tag,provider_name=provider,status=0,supported_parameters=['temperature','reasoning','max_tokens'])]}})
            b.save(root/sn,dict(source_url='https://openrouter.ai/api/v1/models/'+mid+'/endpoints',retrieved_utc='2026-10-24T00:00:00+00:00',sha256=b.sha(root/mn),method='GET',authenticated=False,inference_availability='NOT_VERIFIED',synthetic_fixture=True))
        models.append(dict(id=mid,author_namespace=mid.split('/')[0],provider_tag=tag,response_provider=provider,endpoint_metadata=mn,metadata_source=sn,parameters={'temperature':0.2},comparison_note='OFFLINE example. Same requested temperature does not imply comparable tokenization/default reasoning/cost.'))
    slots=[]
    for arm in ('no_rag','rag'):
        messages=[{'role':'system','content':'RTL only\r\n'},{'role':'user','content':'  synthetic 中文\r\n\t'+arm}]
        (root/(arm+'-messages.json')).write_bytes(json.dumps(messages,ensure_ascii=False,indent=2).encode())
        (root/(arm+'-retrieved.txt')).write_bytes(b'' if arm=='no_rag' else b'SYNTHETIC generic context\r\n')
        for sample in range(1,samples+1):
            for p in models:
                ordinal=len(slots)+1;rn=f'request-{ordinal}.json'
                obj=dict(model=p['id'],messages=messages,stream=False,provider={'only':[p['provider_tag']],'allow_fallbacks':False,'require_parameters':True},**p['parameters'])
                (root/rn).write_bytes(json.dumps(obj,ensure_ascii=False,indent=2).encode())
                slots.append(dict(id='offline-'+str(ordinal),ordinal=ordinal,sample=sample,task='synthetic',condition=arm,model=p['id'],request=rn,messages_file=arm+'-messages.json',retrieved_file=arm+'-retrieved.txt',testbench='tb.sv',reference='ref.sv',spec='spec.txt',expected_checks=213,top='TopModule'))
    data=dict(schema='console-frozen-v3',purpose='OFFLINE_FIXTURE',name='OFFLINE_ONLY',models=models,budget_policy='calls_only',max_calls=len(slots),slots=slots,files={p.name:b.sha(p) for p in root.iterdir()})
    b.save(root/'console-package.json',data)
    return root/'console-package.json'

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.path=fixture(self.root/'packet');self.data=b.read(self.path)
        # Synthetic authorization lives in temp storage and transport is always patched.
        self.data['purpose']='TEST_WITH_MOCKED_TRANSPORT';self.persist()
        self.release=self.root/'release.json';self.approve()
        self.sent=[];self.adapter=SimpleNamespace(route_values=lambda cfg,env:{'endpoint':cfg['endpoint'],'proxy_url':None},send_once=Mock(side_effect=self.reply))
    def persist(self):
        self.path.write_bytes(b.canonical(self.data));self.pkg=b.Package(self.path,self.root/'state')
    def approve(self):
        self.release.write_bytes(b.canonical(dict(decision='CONSOLE_EXECUTION_RELEASE',user_approved=True,owner='exploration',reviewer_thread_id='01a12088-049c-7f32-8167-48be03bcc145',manifest_sha256=self.pkg.identity,bridge_sha256=b.sha(b.__file__),transport_sha256=b.TRANSPORT_SHA,source_hashes=b.bridge_bindings(),max_calls=self.data['max_calls'],budget_policy='calls_only',permitted_slots=[s['id'] for s in self.pkg.slots],automatic_retries=0,request_timeout_seconds=180,model_profiles_sha256=b.digest(b.canonical(self.data['models'])),model_comparison_reviewed=True)))
    def reply(self,raw,route,secret,timeout):
        self.sent.append(raw);obj=json.loads(raw);p=self.pkg.models[obj['model']]
        return dict(outcome='HTTP_OK',request_sha256=b.digest(raw),client_post_invocations=1,body=json.dumps(dict(model=obj['model'],provider=p['response_provider'],choices=[dict(finish_reason='stop',message=dict(role='assistant',content='module TopModule(output x); assign x=0; endmodule'))],usage={'completion_tokens':7,'completion_tokens_details':{'reasoning_tokens':2}})))
    def dispatch(self,slot='offline-1'):
        with patch.object(b,'transport',return_value=self.adapter),patch.object(b,'local_replay',return_value={'fixed_test':'FIXED_TEST_PASS','synthesis':'SYNTH_PASS'}):return self.pkg.dispatch(self.release,slot,'synthetic-secret')
    def change_request(self,index,mutate):
        p=self.path.parent/self.data['slots'][index]['request'];obj=b.read(p);mutate(obj);p.write_bytes(b.canonical(obj));self.data['files'][p.name]=b.sha(p)
        self.path.write_bytes(b.canonical(self.data))
    def test_dynamic_counts_1_2_3_5_and_balanced_samples(self):
        for n in (1,2,3,5):
            p=b.Package(fixture(self.root/str(n),n,2),self.root/'other')
            self.assertEqual(len(p.rows()),n*4);self.assertEqual(len(p.models),n)
    def test_all_three_authors_exact_wire_single_post_per_slot(self):
        before={p.name:b.sha(p) for p in self.path.parent.iterdir()}
        for i in range(1,7):
            r=self.dispatch('offline-'+str(i));self.assertEqual(r['status'],'GENERATED_UNVERIFIED');self.assertIsNone(r['cost'])
            self.assertEqual(r['usage']['completion_tokens_details']['reasoning_tokens'],2)
            self.assertEqual(self.sent[-1],(self.path.parent/self.data['slots'][i-1]['request']).read_bytes())
        self.assertEqual(self.adapter.send_once.call_count,6)
        self.assertEqual(before,{p.name:b.sha(p) for p in self.path.parent.iterdir()})
    def test_author_namespace_is_not_provider(self):
        self.assertEqual(self.pkg.models['deepseek/deepseek-chat-v3.1']['provider_tag'],'deepinfra/fp4')
        self.data['models'][2]['provider_tag']='deepseek'
        with self.assertRaisesRegex(ValueError,'endpoint'):self.persist()
    def test_unsupported_parameter_is_rejected(self):
        self.data['models'][1]['parameters']['seed']=7
        with self.assertRaisesRegex(ValueError,'unsupported'):self.persist()
    def test_unknown_request_control_rejected(self):
        self.change_request(0,lambda o:o.update(models=['fallback/model']))
        with self.assertRaises(ValueError):b.Package(self.path)
    def test_prompt_and_retrieval_bytes_mismatch_rejected(self):
        self.change_request(1,lambda o:o['messages'][0].update(content='changed'))
        with self.assertRaises(ValueError):b.Package(self.path)
    def test_raw_message_file_whitespace_mismatch_rejected(self):
        p=self.path.parent/'different-messages.json';p.write_bytes(json.dumps(b.read(self.path.parent/'no_rag-messages.json')).encode());self.data['files'][p.name]=b.sha(p);self.data['slots'][1]['messages_file']=p.name
        with self.assertRaises(ValueError):self.persist()
    def test_retrieved_segments_mismatch_rejected(self):
        p=self.path.parent/'other.txt';p.write_bytes(b'changed');self.data['files'][p.name]=b.sha(p);self.data['slots'][1]['retrieved_file']=p.name
        with self.assertRaises(ValueError):self.persist()
    def test_unbalanced_and_missing_arm_rejected(self):
        self.data['slots']=self.data['slots'][:3];self.data['max_calls']=3
        with self.assertRaises(ValueError):self.persist()
    def test_duplicate_sample_rejected(self):
        extra=copy.deepcopy(self.data['slots'][0]);extra.update(id='extra',ordinal=7);self.data['slots'].append(extra);self.data['max_calls']=7
        with self.assertRaises(ValueError):self.persist()
    def test_calls_only_no_implicit_cap(self):
        self.assertTrue(all(r['output_budget'] is None for r in self.pkg.rows()))
        self.change_request(0,lambda o:o.update(max_tokens=8192))
        with self.assertRaises(ValueError):b.Package(self.path)
    def test_calls_only_rejects_even_null_cap(self):
        self.data['models'][0]['parameters']['max_tokens']=None
        for i in (0,3):self.change_request(i,lambda o:o.update(max_tokens=None))
        with self.assertRaises(ValueError):self.persist()
    def test_parameter_differences_require_separate_review_binding(self):
        for i in (1,4):self.change_request(i,lambda o:o.update(temperature=0.7))
        self.data['models'][1]['parameters']['temperature']=0.7;self.persist()
        self.approve();r=b.read(self.release);r['model_comparison_reviewed']=False;self.release.write_bytes(b.canonical(r))
        with self.assertRaises(ValueError):self.pkg.gate(self.release,'offline-1')
    def test_unknown_model_rejected(self):
        self.data['slots'][0]['model']='unknown/model'
        with self.assertRaises(ValueError):self.persist()
    def test_model_drift_preserves_body_and_stops(self):self.drift('model','another/model')
    def test_route_drift_preserves_body_and_stops(self):self.drift('provider','Wrong upstream')
    def drift(self,key,value):
        def reply(*args):
            env=self.reply(*args);obj=json.loads(env['body']);obj[key]=value;env['body']=json.dumps(obj);return env
        self.adapter.send_once.side_effect=reply;r=self.dispatch()
        self.assertEqual(r['status'],'MODEL_OR_PROVIDER_MISMATCH');self.assertTrue((self.pkg.state/'offline-1/transport-response.json').exists())
        with self.assertRaises(ValueError):self.dispatch('offline-2')
        self.assertEqual(self.adapter.send_once.call_count,1)
    def test_unknown_timeout_http_error_stop_without_retry(self):
        self.adapter.send_once.side_effect=TimeoutError('synthetic')
        with self.assertRaises(ValueError):self.dispatch()
        with self.assertRaises(ValueError):self.dispatch()
        self.assertEqual(self.adapter.send_once.call_count,1);self.assertEqual(b.read(self.pkg.state/'offline-1/result.json')['status'],'UNKNOWN')
    def test_duplicate_and_skip_order_blocked(self):
        with self.assertRaises(ValueError):self.dispatch('offline-2')
        self.dispatch()
        with self.assertRaises(ValueError):self.dispatch()
        self.assertEqual(self.adapter.send_once.call_count,1)
    def test_cross_package_duplicate_blocked(self):
        self.dispatch();self.data['name']='other-package';self.persist();self.approve()
        with self.assertRaises(ValueError):self.dispatch()
        self.assertEqual(self.adapter.send_once.call_count,1)
    def test_secret_echo_never_persisted(self):
        self.adapter.send_once.side_effect=None;self.adapter.send_once.return_value={'outcome':'HTTP_ERROR','body':'synthetic-secret'}
        with self.assertRaises(ValueError):self.dispatch()
        for p in self.pkg.state.rglob('*'):
            if p.is_file():self.assertNotIn(b'synthetic-secret',p.read_bytes())
    def test_metadata_hash_and_empty_endpoints_block(self):
        p=self.path.parent/'metadata-0.json';p.write_bytes(b'{}')
        with self.assertRaises(ValueError):self.pkg.verify()
    def test_empty_endpoint_metadata_rejected_even_if_hashes_updated(self):
        p=self.path.parent/'metadata-0.json';obj=b.read(p);obj['data']['endpoints']=[];p.write_bytes(b.canonical(obj));self.data['files'][p.name]=b.sha(p)
        src=self.path.parent/'source-0.json';obj=b.read(src);obj['sha256']=b.sha(p);src.write_bytes(b.canonical(obj));self.data['files'][src.name]=b.sha(src)
        with self.assertRaisesRegex(ValueError,'endpoint'):self.persist()
    def test_http_errors_each_stop_without_retry(self):
        self.adapter.send_once.side_effect=None
        self.adapter.send_once.return_value={'outcome':'HTTP_ERROR','status':429,'body':'rate limited','client_post_invocations':1}
        self.assertEqual(self.dispatch()['status'],'HTTP_ERROR')
        with self.assertRaises(ValueError):self.dispatch('offline-2')
        self.assertEqual(self.adapter.send_once.call_count,1)
    def test_real_loopback_three_authors_exact_body_and_no_redirect(self):
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        import threading
        seen=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(302);self.send_header('Location','https://example.invalid');self.end_headers();self.wfile.write(b'redirect')
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for s in self.pkg.slots[:3]:
                raw=(self.path.parent/s['request']).read_bytes()
                r=b.transport().send_once(raw,{'endpoint':f'http://127.0.0.1:{server.server_port}/chat/completions','proxy_url':None},'synthetic-secret',5)
                self.assertEqual(r['outcome'],'REDIRECT_REJECTED');self.assertEqual(r['client_post_invocations'],1);self.assertEqual(seen[-1],raw)
            self.assertEqual(len(seen),3)
        finally:server.shutdown();server.server_close();thread.join()
    def test_no_release_or_fixture_can_execute(self):
        self.release.unlink()
        with self.assertRaises(ValueError):self.dispatch()
        self.assertEqual(self.adapter.send_once.call_count,0)
        self.data['purpose']='OFFLINE_FIXTURE';self.persist();self.approve()
        with self.assertRaises(ValueError):self.dispatch()
    def test_launcher_hash_bound(self):
        import console_cli_v3 as cli
        p=self.root/'Start.ps1';cli.export_launcher(self.path,self.release,p)
        self.assertIn(self.pkg.identity,p.read_text());self.assertIn(b.sha(self.release),p.read_text());self.assertNotIn('synthetic-secret',p.read_text())

class SchoolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.share=self.root/'share';self.share.mkdir();self.home=self.root/'home';self.home.mkdir()
        self.row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
        self.patcher=patch.object(b,'STATE',self.root/'state');self.patcher.start();self.addCleanup(self.patcher.stop)
    def package(self,tool):
        sdc=self.root/'fixture.sdc';sdc.write_text('set_max_delay 10 -from [all_inputs] -to [all_outputs]\n')
        profile=dict(libraries=['/synthetic/library.'+('db' if tool=='dc' else 'lib')],corner='fixture',constraints_reviewed=True,timeout_seconds=600)
        return school.pack(self.row,tool,self.share,profile,sdc)
    def test_all_four_stage_flat_import_ship_and_no_rerun(self):
        for tool in ('dc','genus','vcs','xcelium'):
            record=self.package(tool);source=self.share/record['archive'];dest=stage.stage(source,record['archive_sha256'],self.home)
            self.assertEqual(stage.stage(source,record['archive_sha256'],self.home),dest)
            ast.parse((dest/'console_school_runner_v3.py').read_text(),feature_version=(3,6))
            def execute(manifest,work,started):
                if tool in ('vcs','xcelium'):
                    samples=212 if tool=='vcs' else 211
                    (work/'simulate.log').write_text(f'Mismatches: 0 in {samples} samples\n');(work/'simulate.exit').write_text('0')
                    return dict(status='CHECK_COUNT_DIFFERENT',samples=samples,returncode=0)
                import ece_synth_common as c
                job=b.read(work/'job.json');b.save(work/'execution.json',dict(returncode=0,nonce=job['nonce']))
                for n in c.REQUIRED:
                    p=work/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('SYNTHETIC ARTIFACT ONLY')
                (work/'receipt.txt').write_text('XZY01_SYNTH_V1 '+job['nonce']+' COMPLETE')
                return dict(status='COMPLETED_REVIEW_REQUIRED',returncode=0)
            with patch.object(runner,'__file__',str(dest/'console_school_runner_v3.py')),patch.object(runner.Path,'home',return_value=self.home),patch.object(runner,'school_host',return_value=True),patch.object(runner,'execute',side_effect=execute) as mocked,patch.object(runner.sys,'argv',['runner','run',str(self.share)]):
                runner.main();side=self.share/('return-'+record['key']+'.json')
                result=school.collect(record,side);self.assertTrue(result['verified'])
                if tool in ('vcs','xcelium'):self.assertEqual(result['status'],'CHECK_COUNT_DIFFERENT')
                with patch.object(runner.sys,'argv',['runner','ship',str(self.share)]):runner.main()
                self.assertEqual(mocked.call_count,1)
                with self.assertRaises(FileExistsError):runner.main()
                self.assertEqual(mocked.call_count,1)
                self.assertEqual(school.collect(record,side),result)
            self.assertIn('xzy01-console-v3',school.command(record));self.assertNotIn('find ',school.command(record))
    def test_stage_corruption_and_modified_home_refused(self):
        r=self.package('vcs');archive=self.share/r['archive'];dest=stage.stage(archive,r['archive_sha256'],self.home)
        (dest/'dut.sv').write_bytes(b'changed')
        with self.assertRaises(ValueError):stage.stage(archive,r['archive_sha256'],self.home)
        with archive.open('ab') as f:f.write(b'corrupt')
        with self.assertRaises(ValueError):stage.stage(archive,r['archive_sha256'],self.home)
    def test_stage_traversal_rejected(self):
        p=self.share/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('../bad','bad')
        with self.assertRaises(ValueError):stage.stage(p,b.sha(p),self.home)
    def test_old_history_read_only_and_counts(self):
        self.assertEqual(len(b.history()),336)
        self.assertEqual(b.simulation_verdict('Mismatches: 0 in 211 samples\n',0,213)['fixed_test'],'CHECK_COUNT_DIFFERENT')

class GuiTests(unittest.TestCase):
    def test_hidden_gui_reads_history_and_v3_profiles_no_network(self):
        import tkinter as tk
        from console_gui_v3 import Console
        root=tk.Tk();root.withdraw()
        try:
            with patch.object(b,'transport',side_effect=AssertionError('No network')):
                app=Console(root);root.update();self.assertEqual(len(app.rows),336)
                with tempfile.TemporaryDirectory() as tmp:
                    app.package=b.Package(fixture(Path(tmp)/'packet',2));app.display(app.package.rows());self.assertEqual(len(app.rows),4)
                    app.table.selection_set('0');app.details();self.assertIn('model_profile',app.detail.get('1.0','end'))
        finally:root.destroy()

if __name__=='__main__':unittest.main()
