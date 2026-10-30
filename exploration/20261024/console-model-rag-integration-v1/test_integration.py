"""Synthetic integration tests. Network and EDA prohibited; no real releases saved."""
import copy
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch, Mock
import zipfile
import integration as i
from integration import b,Package
import home_transfer as home
from console import export_launcher

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.packet=self.root/'packet';self.packet.mkdir()
        self.net=patch.object(socket.socket,'connect',side_effect=AssertionError('NO NETWORK'));self.net.start();self.addCleanup(self.net.stop)
        for n,raw in [('spec.txt',b'fixture original\r\n'),('tb.sv',b'module tb; endmodule'),('ref.sv',b'module RefModule; endmodule'),('context.txt',b'\nREFERENCE: synthetic fixture only')]:
            (self.packet/n).write_bytes(raw)
        self.slots=[]
        for arm in ('no_rag','rag'):
            for m in i.MODELS:
                n=len(self.slots)+1
                text='original 中文\r\n'
                if arm=='rag':text+=(self.packet/'context.txt').read_bytes().decode()
                request=dict(model=m,messages=[{'role':'system','content':'RTL only'},{'role':'user','content':text}],stream=False,provider={'only':['openai'],'allow_fallbacks':False,'require_parameters':True},max_tokens=4096,**i.PROFILES[m])
                (self.packet/f'{n}.json').write_bytes(json.dumps(request,ensure_ascii=False).encode())
                self.slots.append(dict(id=f'offline-fixture-{n}',ordinal=n,sample=1,task='fixture',condition=arm,model=m,request=f'{n}.json',testbench='tb.sv',reference='ref.sv',spec='spec.txt',top='TopModule',expected_checks=213))
        self.data=dict(schema='console-frozen-v1',integration='earlier-model-rag-v1',models=list(i.MODELS),model_profiles=i.PROFILES,name='offline-fixture',execution_status='READY_FOR_REVIEW',budget_policy='calls_and_output_cap',max_calls=6,max_cost_usd=1,slot_cost_bounds_usd={s['id']:.1 for s in self.slots},slots=self.slots,contexts={'fixture':'context.txt'})
        self.path=self.packet/'console-package.json';self.refresh()
        self.release=self.root/'synthetic-release.json';self.approve()
    def refresh(self):
        self.data['files']={p.name:b.sha(p) for p in self.packet.iterdir() if p.is_file() and p.name!='console-package.json'}
        self.path.write_bytes(b.canonical(self.data));self.pkg=Package(self.path,self.root/'state')
    def approve(self):
        self.release.write_bytes(b.canonical(dict(decision='CONSOLE_EXECUTION_RELEASE',user_approved=True,owner='exploration',reviewer_thread_id='01a12088-049c-7f32-8167-48be03bcc145',manifest_sha256=self.pkg.identity,bridge_sha256=b.sha(b.__file__),transport_sha256=b.TRANSPORT_SHA,source_hashes=b.bridge_bindings(),integration_sources=i.bindings(),max_calls=6,budget_policy='calls_and_output_cap',max_cost_usd=1,permitted_slots=[s['id'] for s in self.slots],automatic_retries=0,request_timeout_seconds=180)))
    def reply(self,raw,route,secret,timeout):
        obj=json.loads(raw)
        body=dict(model=obj['model'],provider='OpenAI',choices=[dict(finish_reason='stop',message=dict(role='assistant',content='module TopModule(output x); assign x=0; endmodule'))],usage={'prompt_tokens':12,'completion_tokens':20,'cost':.01})
        return dict(outcome='HTTP_OK',request_sha256=b.digest(raw),body=json.dumps(body),client_post_invocations=1)
    def dispatch(self,reply=None,local=None):
        adapter=b.transport();adapter.send_once=Mock(side_effect=reply or self.reply)
        with patch.object(b,'transport',return_value=adapter),patch.object(b,'local_replay',return_value=local or {'fixed_test':'FIXED_TEST_PASS','synthesis':'SYNTH_PASS','infrastructure_stop':False}):
            result=self.pkg.dispatch(self.release,self.slots[0]['id'],'fixture-secret-never-save')
        return result,adapter
    def test_new_models_import_and_original_console_unchanged(self):
        import console_bridge as old
        self.assertNotEqual(old.MODELS,i.MODELS)
        with self.assertRaises(ValueError):old.Package(self.path,self.root/'old-state')
        rows=self.pkg.rows();self.assertEqual(len(rows),6)
        self.assertEqual({r['model'] for r in rows},set(i.MODELS))
        self.assertFalse(self.pkg.state.exists())
    def test_no_release_and_draft_no_reservation(self):
        self.release.unlink()
        with patch.object(b,'transport',side_effect=AssertionError('must not reach transport')):
            with self.assertRaises(ValueError):self.pkg.dispatch(self.release,self.slots[0]['id'],'fixture-secret')
        self.assertFalse((self.pkg.state/self.slots[0]['id']).exists())
        self.data['execution_status']='DRAFT';self.refresh();self.approve()
        with self.assertRaises(ValueError):self.pkg.gate(self.release,self.slots[0]['id'])
    def test_exact_bytes_secret_usage_and_duplicate_block(self):
        result,adapter=self.dispatch()
        self.assertEqual(adapter.send_once.call_count,1)
        self.assertEqual(adapter.send_once.call_args.args[0],(self.packet/'1.json').read_bytes())
        self.assertEqual(result['cost'],.01);self.assertEqual(result['usage']['completion_tokens'],20)
        with self.assertRaises(ValueError):self.pkg.gate(self.release,self.slots[0]['id'])
        self.assertEqual(self.pkg.gate(self.release,self.slots[1]['id'])['id'],self.slots[1]['id'])
        for p in (self.root/'state').rglob('*'):
            if p.is_file():self.assertNotIn(b'fixture-secret-never-save',p.read_bytes())
    def test_unknown_blocks_following_without_retry(self):
        result,adapter=self.dispatch(lambda *a:{'outcome':'UNKNOWN','client_post_invocations':1})
        self.assertEqual(result['status'],'UNKNOWN');self.assertEqual(adapter.send_once.call_count,1)
        for s in self.slots[:2]:
            with self.assertRaises(ValueError):self.pkg.gate(self.release,s['id'])
    def test_403_preserved_and_not_retried(self):
        result,adapter=self.dispatch(lambda *a:{'outcome':'HTTP_ERROR','http_status':403,'client_post_invocations':1})
        self.assertEqual(adapter.send_once.call_count,1);self.assertTrue((self.pkg.state/'STOP.json').exists())
        self.assertEqual(b.read(self.pkg.state/self.slots[0]['id']/'transport-response.json')['http_status'],403)
    def test_function_fail_retained_without_upgrade(self):
        result,_=self.dispatch(local={'fixed_test':'FUNCTION_FAIL','synthesis':'SYNTH_PASS','infrastructure_stop':False})
        self.assertEqual(result['local']['fixed_test'],'FUNCTION_FAIL')
        self.assertEqual(self.pkg.gate(self.release,self.slots[1]['id'])['id'],self.slots[1]['id'])
    def test_changed_message_or_rag_transform_rejected(self):
        for name in ('2.json','4.json'):
            raw=(self.packet/name).read_bytes();obj=json.loads(raw);obj['messages'][-1]['content']+='changed'
            (self.packet/name).write_bytes(b.canonical(obj))
            with self.assertRaises(ValueError):self.refresh()
            (self.packet/name).write_bytes(raw)
    def test_model_reasoning_and_sample_drift_rejected(self):
        obj=b.read(self.packet/'1.json');obj['reasoning']={'effort':'medium'};(self.packet/'1.json').write_bytes(b.canonical(obj))
        with self.assertRaises(ValueError):self.refresh()
    def test_long_prompt_exact_transfer_no_cli_argv(self):
        for n in range(1,7):
            obj=b.read(self.packet/f'{n}.json');obj['messages'][-1]['content']='超长'*70000+('' if n<4 else (self.packet/'context.txt').read_text())
            (self.packet/f'{n}.json').write_bytes(b.canonical(obj))
        self.refresh();self.approve();_,adapter=self.dispatch()
        raw=adapter.send_once.call_args.args[0];self.assertGreater(len(raw),131072);self.assertEqual(raw,(self.packet/'1.json').read_bytes())
        out=self.root/'launcher.ps1';export_launcher(self.path,self.release,out)
        self.assertNotIn('超长',out.read_text());self.assertNotIn('fixture-secret',out.read_text())
        self.assertIn(self.pkg.identity,out.read_text())
    def test_unknown_cost_and_changed_budget_block(self):
        def reply(*args):
            env=self.reply(*args);obj=json.loads(env['body']);del obj['usage']['cost'];env['body']=json.dumps(obj);return env
        self.dispatch(reply)
        with self.assertRaisesRegex(ValueError,'未知费用'):self.pkg.gate(self.release,self.slots[1]['id'])
    def test_school_pack_all_four_new_model_and_flat_import(self):
        self.dispatch();row=self.pkg.rows()[0];shared=self.root/'shared';shared.mkdir()
        sdc=self.root/'fixture.sdc';sdc.write_text('set_max_delay 10 -from [all_inputs] -to [all_outputs]\n')
        with patch.object(b,'STATE',self.root/'state'):
            for tool in ('vcs','xcelium','dc','genus'):
                profile=dict(libraries=['/synthetic/library.'+('db' if tool=='dc' else 'lib')],corner='fixture',constraints_reviewed=True,timeout_seconds=600)
                record=i.school.pack(row,tool,shared,profile,sdc);record=home.prepare(record)
                self.assertIn('xzy01-console-staged',home.command(record,'run'))
                self.assertIn('home_one.py',home.command(record,'check'))
                self.assertIn(' ship ',home.command(record,'ship'))
                with zipfile.ZipFile(record['home_archive']) as z:self.assertIn('home-lock.json',z.namelist())
                if tool!='vcs':continue
                folder=Path(record['local']);manifest=b.read(folder/'console-manifest.json')
                arc=shared/('return-'+record['key']+'.zip')
                result=dict(key=record['key'],manifest_sha256=record['manifest_sha256'],status='CHECK_COUNT_DIFFERENT',returncode=0)
                with zipfile.ZipFile(arc,'x') as z:
                    for n in list(manifest['inputs'])+['console-manifest.json']:z.write(folder/n,n)
                    z.writestr('console-result.json',b.canonical(result));z.writestr('simulate.exit','0');z.writestr('simulate.log','Mismatches: 0 in 212 samples\n')
                side=arc.with_suffix('.json');b.save(side,dict(key=record['key'],manifest_sha256=record['manifest_sha256'],archive_sha256=b.sha(arc)))
                imported=home.collect_flat(record,side);self.assertTrue(imported['verified']);self.assertEqual(imported['status'],'CHECK_COUNT_DIFFERENT')
                self.assertEqual(home.collect_flat(record,side),imported)
                arc.write_bytes(arc.read_bytes()+b'corrupted')
                with self.assertRaises(ValueError):home.collect_flat(record,side)
    def test_alias_mismatch_stops_retains_cost(self):
        def reply(*a):
            env=self.reply(*a);obj=json.loads(env['body']);obj['model']='snapshot-alias';env['body']=json.dumps(obj);return env
        r,_=self.dispatch(reply);self.assertEqual(r['status'],'MODEL_OR_PROVIDER_MISMATCH');self.assertEqual(r['cost'],.01)
    def test_paired_summary_distinguishes_pending_and_real_breakage(self):
        from console import paired_summary
        rows=self.pkg.rows()
        rows[0]['fixed_test']='FUNCTION_FAIL';rows[3]['fixed_test']='FIXED_TEST_PASS'
        rows[1]['fixed_test']='FIXED_TEST_PASS';rows[4]['fixed_test']='FUNCTION_FAIL'
        rows[2]['fixed_test']='CHECK_COUNT_DIFFERENT';rows[5]['fixed_test']='FIXED_TEST_PASS'
        result=paired_summary(rows)['groups']
        self.assertEqual(result[0]['paired']['rag_help'],1);self.assertEqual(result[1]['paired']['rag_harm'],1)
        self.assertEqual(result[2]['paired']['unpaired_or_unevaluated'],1)
    def test_home_stage_exact_archive_and_tamper_refusal(self):
        self.dispatch();shared=self.root/'shared';shared.mkdir();fake_home=self.root/'home';fake_home.mkdir()
        with patch.object(b,'STATE',self.root/'state'):
            record=home.prepare(i.school.pack(self.pkg.rows()[0],'vcs',shared))
        command=home.command(record,'check');code=command.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
        argv=['stage',record['shared_archive'],record['home_sha256'],record['key']]
        with patch.object(Path,'home',return_value=fake_home),patch('sys.argv',argv):
            exec(compile(code,'<offline-stage>','exec'),{})
            staged=fake_home/'xzy01-console-staged'/record['key']
            self.assertEqual(b.sha(staged/'dut.sv'),b.sha(Path(record['local'])/'dut.sv'))
            (staged/'dut.sv').write_bytes(b'tampered')
            with self.assertRaises(SystemExit):exec(compile(code,'<offline-stage>','exec'),{})
        self.assertIn(' && ( ',home.command(record,'run'))

if __name__=='__main__':unittest.main(verbosity=2)
