"""Offline fake responses only. Never use network, production ledger or EDA."""
import contextlib,copy,io,json,os,socket,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
import runner as x
P=Path(__file__).resolve().parent
T=P/'offline-r1';T.mkdir(exist_ok=True)
def deny(*a,**k):raise AssertionError('Network forbidden')
def good(raw,route,timeout):
 req=json.loads(raw)
 return {'outcome':'HTTP_OK','client_post_invocations':1,'request_sha256':x.hashlib.sha256(raw).hexdigest(),'body':json.dumps({'model':req['model'],'provider':'OpenAI','usage':{'prompt_tokens':12,'completion_tokens':8,'cost':0.01,'completion_tokens_details':{'reasoning_tokens':2}},'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'```systemverilog\nmodule TopModule; endmodule\n```'}}]})}
def judge(*a):return {'fixed_test':'FIXED_TEST_PASS','synthesis':'SYNTH_PASS','infrastructure_stop':False}
class Tests(unittest.TestCase):
 def setUp(self):
  self.root=T/self._testMethodName;self.root.mkdir(exist_ok=False)
  self.batch=copy.deepcopy(x.read(P/'batch.json'));self.batch['global_reservations']=str(self.root/'global')
  self.live=self.root/'run';self.calls=0
  self.guard=patch.object(socket.socket,'connect',deny);self.guard.start()
 def tearDown(self):self.guard.stop()
 def send(self,*a):
  self.assertEqual(a[1],{'endpoint':'https://openrouter.ai/api/v1/chat/completions','proxy_url':'http://127.0.0.1:3213'})
  self.calls+=1;return good(*a)
 def run_batch(self,send=None,judge_fn=judge,**kwargs):
  with contextlib.redirect_stdout(io.StringIO()):return x.execute(self.batch,self.live,send or self.send,judge_fn,**kwargs)
 def test_full36_exact_bytes(self):
  r=self.run_batch();self.assertEqual(self.calls,36);self.assertEqual(r['new_reserved'],36);self.assertEqual(r['total_reserved_including_old'],38);self.assertFalse(r['stopped'])
  for s in self.batch['slots']:
   f=self.live/'jobs'/f"{s['ordinal']:03d}"
   self.assertEqual((f/'request.json').read_bytes(),(P/'inputs'/s['request']).read_bytes());self.assertTrue((Path(self.batch['global_reservations'])/f"{s['id']}.json").exists())
  with self.assertRaises(ValueError):self.run_batch()
  self.assertEqual(self.calls,36)
 def test_function_fail_continues(self):
  r=self.run_batch(judge_fn=lambda *a:dict(fixed_test='FUNCTION_FAIL',synthesis='SYNTH_FAIL',infrastructure_stop=False));self.assertEqual(self.calls,36);self.assertFalse(r['stopped'])
 def test_compile_fail_continues(self):
  r=self.run_batch(judge_fn=lambda *a:dict(fixed_test='COMPILE_ERROR',synthesis='SYNTH_FAIL',infrastructure_stop=False));self.assertEqual(self.calls,36);self.assertFalse(r['stopped'])
 def test_http403_stop_no_retry(self):
  def f(*a):e=self.send(*a);e.update(outcome='HTTP_ERROR',http_status=403);return e
  r=self.run_batch(f);self.assertEqual(self.calls,1);self.assertTrue(r['stopped']);self.assertEqual(r['new_not_started'],35)
  with self.assertRaises(ValueError):self.run_batch()
  self.assertEqual(self.calls,1)
 def test_unknown_stops(self):
  def f(*a):e=self.send(*a);e['outcome']='UNKNOWN';return e
  self.assertTrue(self.run_batch(f)['stopped']);self.assertEqual(self.calls,1)
 def test_provider_drift(self):
  def f(*a):e=self.send(*a);b=json.loads(e['body']);b['provider']='Other';e['body']=json.dumps(b);return e
  self.assertTrue(self.run_batch(f)['stopped']);self.assertEqual(self.calls,1)
 def test_model_drift(self):
  def f(*a):e=self.send(*a);b=json.loads(e['body']);b['model']='alternate';e['body']=json.dumps(b);return e
  self.assertTrue(self.run_batch(f)['stopped']);self.assertEqual(self.calls,1)
 def test_truncated_response(self):
  def f(*a):e=self.send(*a);b=json.loads(e['body']);b['choices'][0]['finish_reason']='length';e['body']=json.dumps(b);return e
  self.assertTrue(self.run_batch(f)['stopped']);self.assertEqual(self.calls,1)
 def test_extraction_error_preserved(self):
  def f(*a):e=self.send(*a);b=json.loads(e['body']);b['choices'][0]['message']['content']='not RTL';e['body']=json.dumps(b);return e
  r=self.run_batch(f);self.assertEqual(r['counts'].get('EXTRACTION_ERROR'),1);self.assertTrue(r['stopped'])
 def test_tool_error_stops(self):
  r=self.run_batch(judge_fn=lambda *a:dict(fixed_test='TOOL_OR_RECEIPT_ERROR',synthesis='NOT_RUN',infrastructure_stop=True));self.assertTrue(r['stopped']);self.assertEqual(self.calls,1)
 def test_check_count_mismatch_stops(self):
  r=self.run_batch(judge_fn=lambda *a:dict(fixed_test='CHECK_COUNT_DIFFERENT',synthesis='SYNTH_PASS',infrastructure_stop=False));self.assertTrue(r['stopped']);self.assertEqual(self.calls,1)
 def test_real_local_adapter_with_mock_process(self):
  import rtl_lab
  self.assertEqual(Path(rtl_lab.__file__).resolve(),(P/'reuse/rtl_lab.py').resolve())
  f=self.root/'fixture';f.mkdir()
  for n in ('dut.sv','reference.sv','testbench.sv'):(f/n).write_text('module TopModule; endmodule')
  commands=[]
  def process(argv,cwd,timeout,env=None):
   commands.append(argv)
   self.assertNotIn('OPENROUTER_API_KEY',env)
   if argv[0]=='wsl.exe':
    (Path(cwd)/'netlist.json').write_text('{}');(Path(cwd)/'netlist.v').write_text('module TopModule; endmodule')
   return {'returncode':0,'timeout':False,'output_limit':False,'stdout':'Mismatches: 0 in 3 samples\r\n','stderr':''}
  with patch.object(rtl_lab,'run_process',process):r=x.bridge.local_replay(f,f/'local',3)
  self.assertEqual(r['fixed_test'],'FIXED_TEST_PASS');self.assertEqual(r['synthesis'],'SYNTH_PASS');self.assertEqual(len(commands),3)
  self.assertTrue((f/'local/result.json').exists())
 def test_source_drift_rejected(self):
  original=x.sha
  with patch.object(x,'sha',lambda p:'bad' if str(p).endswith('runner.py') else original(p)):
   with self.assertRaises(ValueError):x.verify()
 def test_keyboard_interruption_preserved(self):
  def f(*a):self.calls+=1;raise KeyboardInterrupt()
  r=self.run_batch(f);self.assertTrue(r['stopped']);self.assertEqual(r['counts']['UNKNOWN'],1)
 def test_cross_entry_reservation(self):
  s=self.batch['slots'][0];x.save(Path(self.batch['global_reservations'])/f"{s['id']}.json",{'reserved':'other'})
  with self.assertRaises(ValueError):self.run_batch()
  self.assertEqual(self.calls,0)
 def test_exclusive_lock(self):
  x.save(self.live/'exclusive.lock',{'pid':'other'})
  with self.assertRaises(FileExistsError):self.run_batch()
  self.assertEqual(self.calls,0);self.assertEqual(x.read(self.live/'exclusive.lock'),{'pid':'other'})
 def test_long_paths_block_before_post(self):
  self.live=self.root/('x'*110)
  with self.assertRaises(ValueError):self.run_batch()
  self.assertEqual(self.calls,0)
 def test_preprobe_write_failure(self):
  with patch.object(x,'write',side_effect=OSError('mock disk failure')):
   with self.assertRaises(OSError):self.run_batch()
  self.assertEqual(self.calls,0)
 def test_response_open_failure_before_reservation(self):
  original=Path.open
  def opened(path,*a,**kw):
   if path.name=='transport-response.json' and (self.live/'RUN_STARTED.json').exists():raise FileNotFoundError('mock path')
   return original(path,*a,**kw)
  with patch.object(Path,'open',opened):
   with self.assertRaises(FileNotFoundError):self.run_batch()
  self.assertEqual(self.calls,0);self.assertFalse(Path(self.batch['global_reservations']).exists())
 def test_response_save_failure_keeps_secondary(self):
  original=os.fsync
  def f(*a):
   e=self.send(*a)
   # Fail only first fsync after send, then preserve fallback and STOP.
   def bad(fd):os.fsync=original;raise OSError('mock disk flush')
   os.fsync=bad;return e
  try:r=self.run_batch(f)
  finally:os.fsync=original
  self.assertTrue(r['stopped']);self.assertEqual(self.calls,1);self.assertTrue((self.live/'jobs/001/receipt-write-error.json').exists())
 def test_result_save_failure_no_resume(self):
  original=x.save
  def save(p,obj):
   if Path(p).name=='result.json':raise OSError('mock result disk')
   original(p,obj)
  with patch.object(x,'save',save):
   with self.assertRaises(OSError):self.run_batch()
  self.assertEqual(self.calls,1)
  with self.assertRaises(ValueError):self.run_batch()
  self.assertEqual(self.calls,1)
 def test_abrupt_crash_after_reservation(self):
  batch_file=self.root/'batch.json';x.save(batch_file,self.batch)
  code="import os,sys; from pathlib import Path; import runner as x; b=x.read(sys.argv[1]); x.execute(b,Path(sys.argv[2]),lambda *a:os._exit(23),lambda *a:{})"
  p=subprocess.run([sys.executable,'-B','-c',code,str(batch_file),str(self.live)],cwd=P,capture_output=True,timeout=20)
  self.assertEqual(p.returncode,23);self.assertTrue((self.live/'exclusive.lock').exists())
  self.assertEqual(x.summary(self.live,self.batch)['counts']['UNKNOWN'],1)
  with self.assertRaises(FileExistsError):self.run_batch()
  self.assertEqual(self.calls,0)
 def test_gate_old_release_rejected(self):
  # Real gate/source checks, no credential/network. Old release cannot unlock new IDs.
  with self.assertRaises(ValueError):x.gate(x.R/'validation/main36-release-20261029-v1/release.json')
  with self.assertRaises(ValueError):x.gate(x.R/'validation/main36-script-review-20261029-v1/release.json')
 def test_proxy_connect_target_single_post(self):
  for status in (200,302,403,429,500):
   with self.subTest(status=status):
    events=[]
    class Response:
     def __init__(self):self.status=status
     def read(self,limit):return b'{}'
     def getheader(self,name):return None
    class Conn:
     def __init__(self,host,port,**kw):events.append(('endpoint',host,port))
     def set_tunnel(self,host,port):events.append(('CONNECT',host,port))
     def request(self,method,target,body,headers):events.append((method,target,body))
     def getresponse(self):return Response()
     def close(self):events.append(('close',))
    raw=b'{"offline_fixture":true}'
    with patch.object(x.transport.http.client,'HTTPSConnection',Conn),patch.object(x.transport.http.client,'HTTPConnection',deny),patch.object(x.transport.ssl,'create_default_context',lambda:object()):
     env=x.transport.send_once(raw,self.batch['route'],'OFFLINE_SYNTHETIC_ONLY',180)
    self.assertEqual(events[:3],[('endpoint','127.0.0.1',3213),('CONNECT','openrouter.ai',443),('POST','/api/v1/chat/completions',raw)])
    self.assertEqual(len(events),4);self.assertEqual(env['client_post_invocations'],1)
    self.assertEqual(env['outcome'],'HTTP_OK' if status==200 else ('REDIRECT_REJECTED' if status==302 else 'HTTP_ERROR'))
 def test_proxy_unavailable_no_direct_fallback(self):
  events=[]
  class Conn:
   def __init__(self,host,port,**kw):events.append((host,port))
   def set_tunnel(self,host,port):events.append(('CONNECT',host,port))
   def request(self,*a,**k):events.append(('POST',));raise ConnectionRefusedError('offline refusal')
   def close(self):pass
  with patch.object(x.transport.http.client,'HTTPSConnection',Conn),patch.object(x.transport.http.client,'HTTPConnection',deny),patch.object(x.transport.ssl,'create_default_context',lambda:object()):
   env=x.transport.send_once(b'{}',self.batch['route'],'OFFLINE_SYNTHETIC_ONLY',180)
  self.assertEqual(env['outcome'],'UNKNOWN');self.assertEqual(len(events),3);self.assertEqual(events[0],('127.0.0.1',3213))
 def test_proxy_env_not_inherited(self):
  cfg=x.read(P/'route-config.json')
  self.assertIsNone(cfg['proxy_env'])
  self.assertEqual(x.transport.route_values(cfg,{'HTTP_PROXY':'http://other:8','HTTPS_PROXY':'http://other:8'}),self.batch['route'])
 def test_route_change_rejected(self):
  original=x.read
  def altered(p):
   v=original(p)
   if Path(p).name=='batch.json':v['route']['proxy_url']=None
   return v
  with patch.object(x,'read',altered):
   with self.assertRaises(ValueError):x.verify()
 def test_request_no_caps_or_prompt_changes(self):
  for s in self.batch['slots']:
   obj=x.read(P/'inputs'/s['request']);self.assertFalse({'max_tokens','max_completion_tokens'}&obj.keys());self.assertEqual(obj['messages'],x.read(P/'inputs'/s['messages_file']))

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
 with (P/'test-output-r1.txt').open('x',encoding='utf-8') as out:
  result=unittest.TextTestRunner(stream=out,verbosity=2).run(suite)
 x.save(P/'offline-audit-r1.json',{'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'network_calls':0,'model_calls':0,'eda_calls':0,'fixture_mode':'Injected local synthetic responses, no server; subprocess only os._exit crash witness; real local adapter with mocked bounded process','source_lock_sha256':x.sha(P/'source-lock-r1.json')})
 print(json.dumps(x.read(P/'offline-audit-r1.json')));sys.exit(0 if result.wasSuccessful() else 1)
