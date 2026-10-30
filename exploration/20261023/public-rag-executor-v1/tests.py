"""Pure offline transport/EDA mocks; no socket, model, compiler or simulator call."""
import json,os,sys,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
import core,dispatch,http_once
ROOT=None
SLOTS=core.read(core.BATCH/'slots.json')
RTL='module TopModule(input clk,input reset,input [2:0] s,output fr2,fr1,fr0,dfr); assign {fr2,fr1,fr0,dfr}=0; endmodule'
def response(slot,content=RTL,finish='stop',tokens=40,model=None):
 return {'outcome':'HTTP_OK','request_sha256':slot['request_sha256'],'body':json.dumps({'id':'OFFLINE_MOCK','model':model or slot['model'],'usage':{'prompt_tokens':100,'completion_tokens':tokens},'choices':[{'message':{'role':'assistant','content':content},'finish_reason':finish}]})}
def judged(s,f,r):return {'status':'REFERENCE_PASS','stage':'original_test','stop':False,'mock':True}
class Tests(unittest.TestCase):
 def setUp(self):self.root=ROOT/self._testMethodName;self.root.mkdir()
 def execute(self,transport,count=2,judge=judged,**kw):return dispatch.execute(self.root/'run',SLOTS[:count],'OFFLINE_MOCK',transport,judge_fn=judge,**kw)
 def test_exact_payload_reserve_before_send(self):
  calls=[]
  def transport(s,f,t):
   self.assertTrue((self.root/'run/reservations'/f"{s['id']}.json").exists());self.assertEqual((f/'request.json').read_bytes(),(core.BATCH/s['request']).read_bytes());calls.append(s['id']);return response(s)
  summary=self.execute(transport);self.assertEqual(len(calls),2);self.assertEqual(summary['reserved'],2);self.assertEqual(summary['complete_http_returns'],2);self.assertEqual(summary['not_started'],0)
 def test_403_stops_remaining_without_retry(self):
  calls=[]
  def t(s,f,x):calls.append(s['id']);return {'outcome':'HTTP_ERROR','http_status':403}
  r=self.execute(t);self.assertEqual(len(calls),1);self.assertEqual(r['reserved'],1);self.assertEqual(r['not_started'],1);self.assertEqual(r['counts']['SERVICE_ERROR'],1)
  r=self.execute(t);self.assertEqual(len(calls),1)
 def test_unknown_stops_and_never_resends(self):
  calls=[]
  def t(s,f,x):calls.append(s['id']);raise TimeoutError()
  r=self.execute(t);self.assertEqual(r['unknown'],1);self.assertEqual(r['not_started'],1);self.execute(t);self.assertEqual(len(calls),1)
 def test_crash_reserved_recovery(self):
  l=core.Ledger(self.root/'run',SLOTS[:2],'OFFLINE_MOCK');l.reserve(SLOTS[0],SLOTS[0]['request_sha256']);calls=[]
  r=self.execute(lambda *x:calls.append(x));self.assertEqual(r['unknown'],1);self.assertEqual(calls,[])
 def test_crash_after_response_keeps_complete_return(self):
  l=core.Ledger(self.root/'run',SLOTS[:2],'OFFLINE_MOCK');l.reserve(SLOTS[0],SLOTS[0]['request_sha256']);core.save(l.root/'jobs'/f"{SLOTS[0]['ordinal']:03d}"/'transport-response.json',response(SLOTS[0]))
  r=self.execute(lambda *x:self.fail('must not resend'));self.assertEqual(r['unknown'],0);self.assertEqual(r['complete_http_returns'],1);self.assertEqual(r['counts']['RECOVERY_RESPONSE_UNPROCESSED'],1)
 def test_postprocessing_error_keeps_http_return(self):
  def bad(*a):raise ValueError('mock judge failure')
  r=self.execute(lambda s,f,t:response(s),judge=bad);self.assertEqual(r['unknown'],0);self.assertEqual(r['complete_http_returns'],1);self.assertEqual(r['counts']['POSTPROCESSING_ERROR'],1)
 def test_stage_isolation_length_retained(self):
  r=self.execute(lambda s,f,t:response(s,finish='length'));self.assertEqual(r['counts']['EXTRACTION_ERROR'],2)
  rows=[core.read(p) for p in (self.root/'run/results').glob('*.json')];self.assertTrue(all(x['stage']=='extraction' for x in rows));self.assertEqual(r['complete_http_returns'],2)
 def test_multiple_blocks_no_cherry_pick(self):
  r=self.execute(lambda s,f,t:response(s,'```sv\n'+RTL+'\n```\n```sv\n'+RTL+'\n```'));self.assertEqual(r['counts']['EXTRACTION_ERROR'],2)
 def test_128k_exact_and_one_over(self):
  exact=RTL+'\n//'+'x'*(131072-len((RTL+'\n//').encode()));self.assertEqual(len(exact.encode()),131072);core.extract(exact)
  try:core.extract(exact+'x');self.fail('over limit accepted')
  except Exception as e:self.assertEqual(getattr(e,'status',None),'EXTRACTION_ERROR');self.assertEqual(e.stage,'extraction')
 def test_usage_over8192_stops(self):
  r=self.execute(lambda s,f,t:response(s,tokens=8193));self.assertEqual(r['counts']['BUDGET_VIOLATION'],1);self.assertEqual(r['not_started'],1)
 def test_usage_invalid_does_not_crash_ledger(self):
  r=self.execute(lambda s,f,t:response(s,tokens='unknown'));self.assertEqual(r['counts']['SERVICE_PROTOCOL_ERROR'],1);self.assertEqual(r['usage_unavailable_attempts'],1)
 def test_model_mismatch_no_substitution(self):
  r=self.execute(lambda s,f,t:response(s,model='gpt-other'));self.assertEqual(r['counts']['MODEL_ID_MISMATCH'],1)
 def test_request_tamper_prevents_reservation(self):
  def loader(s):d=core.read(core.BATCH/s['request']);d['max_completion_tokens']=9999;return json.dumps(d).encode()
  with self.assertRaises(AssertionError):self.execute(lambda *a:self.fail('sent'),request_loader=loader)
  self.assertEqual(len(list((self.root/'run/reservations').glob('*'))),0)
 def test_actual_sent_payload_hash_mismatch(self):
  def t(s,f,x):e=response(s);e['request_sha256']='0'*64;return e
  r=self.execute(t);self.assertEqual(r['counts']['PAYLOAD_MISMATCH'],1)
 def test_gate_change_stops_before_send(self):
  r=self.execute(lambda *a:self.fail('sent'),gate=lambda:{'ready':False});self.assertEqual(r['reserved'],0);self.assertTrue(r['stopped'])
 def test_attempt240_cap_and_duplicate(self):
  l=core.Ledger(self.root/'run',SLOTS,'OFFLINE_MOCK')
  for s in SLOTS:l.reserve(s,s['request_sha256']);l.finish(s,dict(status='EXTRACTION_ERROR',complete_http_return=True,usage=None))
  with self.assertRaises(AssertionError):l.reserve(SLOTS[0],SLOTS[0]['request_sha256'])
  self.assertEqual(len(l.reservations()),240)
 def test_duplicate_slot_before_cap(self):
  l=core.Ledger(self.root/'run',SLOTS[:2],'OFFLINE_MOCK');s=SLOTS[0];l.reserve(s,s['request_sha256']);l.finish(s,dict(status='EXTRACTION_ERROR'))
  with self.assertRaises(FileExistsError):l.reserve(s,s['request_sha256'])
  self.assertEqual(len(l.reservations()),1)
 def test_concurrent_lock_rejected(self):
  a=core.Ledger(self.root/'run',SLOTS[:2],'OFFLINE_MOCK');a.lock()
  try:
   b=core.Ledger(self.root/'run',SLOTS[:2],'OFFLINE_MOCK')
   with self.assertRaises(FileExistsError):b.lock()
  finally:a.unlock()
 def test_wall_deadline_no_send(self):
  l=core.Ledger(self.root/'run',SLOTS[:2],'OFFLINE_MOCK');now=core.read(l.root/'identity.json')['start_epoch']
  with patch('dispatch.time.time',return_value=now+12001):r=self.execute(lambda *a:self.fail('sent'))
  self.assertEqual(r['reserved'],0)
 def test_judge_mock_compile_failure_stage(self):
  f=self.root/'job';f.mkdir()
  def p(argv,folder,label,timeout,env):return dict(returncode=1,limit_reason=None,launch_error=None)
  r=core.judge(SLOTS[0],f,RTL,p);self.assertEqual(r['status'],'COMPILE_ERROR');self.assertEqual(r['stage'],'compile')
 def test_judge_mock_receipt_rejects_exit0_timeout(self):
  for n,text,expected in [('ok','Mismatches: 0 in 8 samples\r\n','REFERENCE_PASS'),('bad','Mismatches: 2 in 8 samples\n','REFERENCE_FAIL'),('zero','Mismatches: 0 in 0 samples\n','SIM_ERROR_OR_TIMEOUT'),('timeout','TIMEOUT\nMismatches: 0 in 8 samples\n','SIM_ERROR_OR_TIMEOUT')]:
   f=self.root/n;f.mkdir()
   def p(argv,folder,label,timeout,env):
    core.save_bytes(folder/(label+'.stdout.bin'),text.encode());return dict(returncode=0,limit_reason=None,launch_error=None)
   self.assertEqual(core.judge(SLOTS[0],f,RTL,p)['status'],expected)
 def test_timeout_after_response_preserves_known_return(self):
  def t(slot,folder,timeout):core.save(folder/'transport-response.json',response(slot));return {'outcome':'UNKNOWN'}
  r=self.execute(t);self.assertEqual(r['complete_http_returns'],1);self.assertEqual(r['unknown'],0);self.assertEqual(r['counts']['POSTPROCESSING_ERROR'],1)
 def test_process_interrupt_cleans_child_without_real_process(self):
  f=self.root/'job';f.mkdir()
  class Proc:
   pid=12345
   def poll(self):return None
   def kill(self):pass
   def wait(self,timeout):return 1
  with patch('core.subprocess.Popen',return_value=Proc()),patch('core.subprocess.run') as kill,patch('core.time.sleep',side_effect=KeyboardInterrupt()):
   with self.assertRaises(KeyboardInterrupt):core.bounded_process(['mock-native'],f,'mock',15,core.clean_env())
   self.assertEqual(kill.call_count,1);self.assertIn('/T',kill.call_args.args[0])
 def worker(self,name,body=None,error=None):
  f=self.root/name;f.mkdir();request=f/'request.json';request.write_bytes((core.BATCH/SLOTS[0]['request']).read_bytes());core.save(f/'route.json',{'endpoint':'https://offline.invalid/v1/chat/completions'});captured=[]
  class Resp:
   status=200
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,n):return body[:n]
  class Opener:
   def open(self,req,timeout):
    captured.append(req.data)
    if error:raise error
    return Resp()
  args=['http_once.py',str(request),str(f/'route.json'),str(f/'result.json'),'180']
  with patch.object(sys,'argv',args),patch.dict(os.environ,{'RTL_RAG_SECRET':'MOCK_SECRET_NOT_REAL'}),patch('urllib.request.build_opener',return_value=Opener()):http_once.main()
  self.assertEqual(captured,[request.read_bytes()]);return core.read(f/'result.json')
 def test_worker_exact_wire_bytes(self):
  r=self.worker('wire',response(SLOTS[0])['body'].encode());self.assertEqual(r['outcome'],'HTTP_OK');self.assertEqual(r['request_sha256'],SLOTS[0]['request_sha256'])
 def test_worker403_no_retry(self):
  r=self.worker('403',error=urllib.error.HTTPError('https://offline.invalid',403,'no',{},None));self.assertEqual(r['outcome'],'HTTP_ERROR');self.assertEqual(r['http_status'],403)
 def test_worker_disconnect_unknown(self):
  r=self.worker('disconnect',error=urllib.error.URLError('offline'));self.assertEqual(r['outcome'],'UNKNOWN')
 def test_worker_body_boundary_and_secret_redaction(self):
  self.assertEqual(self.worker('over',b'x'*1048577)['outcome'],'RESPONSE_SIZE_LIMIT');self.assertEqual(self.worker('exact',b'x'*1048576)['outcome'],'HTTP_OK')
  r=self.worker('secret',b'MOCK_SECRET_NOT_REAL');self.assertEqual(r['outcome'],'SECRET_ECHO_REDACTED');self.assertNotIn('MOCK_SECRET_NOT_REAL',json.dumps(r))
 def test_no_redirect(self):self.assertIsNone(http_once.NoRedirect().redirect_request(None,None,None,None,None,None))
 def test_all240_frozen_payloads(self):
  for s in SLOTS:dispatch.validate_payload(s,(core.BATCH/s['request']).read_bytes())

if __name__=='__main__':
 ROOT=Path(sys.argv[1]).resolve();ROOT.mkdir();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);result=unittest.TextTestRunner(verbosity=2).run(suite)
 core.save(ROOT/'test-summary.json',{'kind':'OFFLINE_TRANSPORT_AND_EDA_MOCKS_ONLY','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'success':result.wasSuccessful(),'model_calls':0,'real_http_requests':0,'real_compile_sim_calls':0,'source_sha256':{p.name:core.sha(p) for p in [Path(__file__),core.HERE/'core.py',core.HERE/'dispatch.py',core.HERE/'http_once.py']}})
 raise SystemExit(0 if result.wasSuccessful() else 1)
