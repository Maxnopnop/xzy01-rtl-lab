"""Finite loopback-only audit. No credentials/account/external API; no HDL tools."""
import collections,http.server,json,socket,threading,time,traceback,copy,ast,os
from pathlib import Path
from unittest.mock import patch
import core,runner,ledger
P=Path(__file__).resolve().parent
def main():
    root=P/'mock';root.mkdir(exist_ok=False);slots=runner.verify_inputs();counts=collections.Counter();records=[];checks={};modes=['400','403','429','502','embedded502','redirect','interrupted','timeout']
    core.save(root/'source-at-test.json',core.read(P/'source-lock.json'));core.save(root/'start.json',{'utc':core.utc(),'plan_sha256':core.sha(P/'offline-test-plan.json'),'addendum_sha256':core.sha(P/'test-plan-addendum.json'),'model_calls':0})
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            mode=self.path.split('/')[1];raw=self.rfile.read(int(self.headers['Content-Length']));counts[mode]+=1
            core.save_bytes(root/'captures'/mode/f'{counts[mode]:03d}.bin',raw)
            records.append({'mode':mode,'sha256':core.digest(raw),'synthetic_auth':self.headers.get('Authorization')=='Bearer OFFLINE_SYNTHETIC_TOKEN_ONLY'})
            if mode=='timeout':time.sleep(1);self.close_connection=True;return
            if mode=='interrupted':
                self.send_response(200);self.send_header('Content-Length','9000');self.end_headers();self.wfile.write(b'{"partial":');self.wfile.flush();self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            if mode=='redirect':
                self.send_response(307);self.send_header('Location',f'http://127.0.0.1:{self.server.server_port}/redirect_target/chat/completions');self.send_header('Content-Length','0');self.end_headers();return
            obj=json.loads(raw)
            if mode.isdigit():self.send_response(int(mode));body={'error':{'message':'OFFLINE fixture'}}
            else:
                self.send_response(200);body={'id':'OFFLINE-FIXTURE','model':obj['model'],'provider':'OpenAI','choices':[{'message':{'role':'assistant','content':'module TopModule; endmodule'},'finish_reason':'stop'}]}
                if mode=='embedded502':body['error']={'code':502,'message':'OFFLINE fixture error'}
                elif counts[mode]%2:body['usage']={'prompt_tokens':10,'completion_tokens':9000,'total_tokens':9010,'completion_tokens_details':{'reasoning_tokens':3},'cost':0.01}
            data=json.dumps(body).encode();self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    def sender(mode):
        cfg=dict(core.read(P/'route.json'),endpoint=f'http://127.0.0.1:{server.server_port}/{mode}/chat/completions',proxy_url=None)
        return lambda s,f,t:runner.send(s,f,.25 if mode=='timeout' else 2,cfg,True)
    def fake_judge(*args):return {'status':'MOCK_ONLY_NOT_EDA','stage':'fixture','stop':False}
    bind={'test_source':core.sha(P/'source-lock.json')}
    try:
        first=runner.execute(root/'success',slots,'MOCK',sender('success'),fake_judge,run_binding=bind)
        second=runner.execute(root/'success',slots,'MOCK',sender('success'),fake_judge,run_binding=bind)
        checks['96_cap_repeat_zero_posts']=counts['success']==96 and first['reserved']==second['reserved']==96 and second['not_started']==0
        checks['96_full_frozen_bytes']=all((root/'captures/success'/f'{s["ordinal"]:03d}.bin').read_bytes()==(runner.BATCH/s['request']).read_bytes() for s in slots)
        results=[]
        for mode in modes:
            rr=root/'failures'/mode
            a=runner.execute(rr,slots[:2],'MOCK',sender(mode),fake_judge,run_binding=bind)
            if mode=='timeout':time.sleep(1.05)
            b=runner.execute(rr,slots[:2],'MOCK',sender(mode),fake_judge,run_binding=bind)
            expected='UNKNOWN' if mode in ['timeout','interrupted'] else 'SERVICE_ERROR'
            result=core.read(rr/'results'/f"{slots[0]['id']}.json")
            passed=counts[mode]==1 and a['reserved']==b['reserved']==1 and b['stopped'] and result['status']==expected
            results.append({'mode':mode,'passed':passed,'status':result['status'],'posts':counts[mode],'remaining':b['not_started']})
        checks['failure_stop_and_reentry']=all(r['passed'] for r in results);checks['redirect_not_followed']=counts['redirect_target']==0
        core.save(root/'failure-matrix.json',results)
        checks['unknown_usage_stays_null']=all(v is None for v in core.read(root/'success/results'/f"{slots[1]['id']}.json")['usage_normalized']['values'].values())
        ll=ledger.Ledger(root/'success',slots,'MOCK',bind);ll.lock()
        try:
            try:ll.reserve(slots[0],slots[0]['request_sha256']);checks['97th_rejected']=False
            except AssertionError:checks['97th_rejected']=True
        finally:ll.unlock()
        calls=[]
        for scenario in ['pending','missing_STOP']:
            rr=root/scenario;ll=ledger.Ledger(rr,slots[:2],'MOCK',bind);ll.lock();ll.reserve(slots[0],slots[0]['request_sha256'])
            if scenario=='missing_STOP':ll.finish(slots[0],{'status':'SERVICE_ERROR','stage':'transport','stop':True,'complete_http_return':False,'usage':None})
            ll.unlock()
            before=len(calls);res=runner.execute(rr,slots[:2],'MOCK',lambda *x:calls.append(1),fake_judge,run_binding=bind)
            checks[scenario+'_no_send']=len(calls)==before and res['stopped'] and res['reserved']==1
            if scenario=='pending':checks['pending_UNKNOWN']=res['unknown']==1
        bad=copy.deepcopy(slots[:2]);bad[0]['request_sha256']='0'*64
        try:runner.execute(root/'hash_drift',bad,'MOCK',lambda *x:calls.append(1),fake_judge,run_binding=bind);checks['hash_drift']=False
        except AssertionError:checks['hash_drift']=not calls and not list((root/'hash_drift/reservations').glob('*.json'))
        ll=ledger.Ledger(root/'exclusive',slots[:2],'MOCK',bind);ll.lock()
        try:
            try:runner.execute(root/'exclusive',slots[:2],'MOCK',lambda *x:calls.append(1),fake_judge,run_binding=bind);checks['exclusive']=False
            except FileExistsError:checks['exclusive']=not calls and (root/'exclusive/exclusive.lock').exists()
        finally:ll.unlock()
        with patch.object(core,'size',return_value=runner.MAX_DISK):
            res=runner.execute(root/'disk_limit',slots[:2],'MOCK',lambda *x:calls.append(1),fake_judge,run_binding=bind)
        checks['disk_stop_before_reservation']=res['stopped'] and res['reserved']==0 and not calls
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':''}):checks['empty_credential_false']=runner.preflight()['credential_present'] is False
        # No batch elapsed-time check exists: an old identity still runs a local fixture once.
        rr=root/'aged';ll=ledger.Ledger(rr,slots[:1],'MOCK',bind);ll.lock();ll.unlock();identity=core.read(rr/'identity.json');identity['start_epoch']=1
        (rr/'identity.json').write_text(json.dumps(identity))
        def local_no_http(s,f,t):
            return {'outcome':'HTTP_OK','request_sha256':s['request_sha256'],'body':json.dumps({'model':s['wire_model'],'provider':'OpenAI','choices':[{'message':{'role':'assistant','content':'module TopModule; endmodule'},'finish_reason':'stop'}]})}
        aged=runner.execute(rr,slots[:1],'MOCK',local_no_http,fake_judge,run_binding=bind);checks['no_batch_wall_cap']=aged['reserved']==1 and not aged['stopped']
        # Text boundary/extraction and protocol checks, in-memory responses only.
        tested=[]
        exact='module TopModule; endmodule\n//'+('x'*(131072-len('module TopModule; endmodule\n//')))
        for name,content,want,stop in [('exact128',exact,'MOCK_ONLY_NOT_EDA',False),('over128',exact+'x','RESOURCE_LIMIT',True),('multiblock','```verilog\nmodule TopModule; endmodule\n```\n```sv\nmodule X;endmodule\n```','EXTRACTION_ERROR',False),('unsafe','module TopModule; initial $display(1); endmodule','RTL_REJECTED',False)]:
            folder=root/'unit'/name;folder.mkdir(parents=True);env=local_no_http(slots[0],folder,0);body=json.loads(env['body']);body['choices'][0]['message']['content']=content;env['body']=json.dumps(body)
            result=core.process_response(slots[0],folder,env,fake_judge);tested.append({'case':name,'status':result['status'],'stop':result['stop']});checks[name]=result['status']==want and result['stop']==stop
        for name,key,value,want in [('model_mismatch','model','other','MODEL_ID_MISMATCH'),('provider_mismatch','provider','Other','PROVIDER_ID_MISMATCH')]:
            folder=root/'unit'/name;folder.mkdir();env=local_no_http(slots[0],folder,0);body=json.loads(env['body']);body[key]=value;env['body']=json.dumps(body);r=core.process_response(slots[0],folder,env,fake_judge);checks[name]=r['status']==want and r['stop']
        checks['http_resource_stop']=core.process_response(slots[0],root,{'outcome':'RESPONSE_SIZE_LIMIT'},fake_judge)['stop']
        for name,want,stop in [('compile_timeout','INFRASTRUCTURE_ERROR',True),('simulate_timeout','INFRASTRUCTURE_ERROR',True),('tb_timeout','RESOURCE_LIMIT',True),('compile_error','COMPILE_ERROR',False)]:
            folder=root/'unit'/name;folder.mkdir();phases=[]
            def fake_process(argv,folder,label,timeout,env):
                phases.append(label);limit='timeout' if name==label+'_timeout' else None
                if label=='simulate':core.save_bytes(folder/'simulate.stdout.bin',b'TIMEOUT\n' if name=='tb_timeout' else b'Mismatches: 0 in 1 samples\n')
                return {'returncode':1 if name=='compile_error' else 0,'limit_reason':limit,'launch_error':None}
            result=core.judge(slots[0],folder,'module TopModule; endmodule',process=fake_process);checks[name]=result['status']==want and result['stop']==stop
            tested.append({'case':name,'status':result['status'],'stop':result['stop'],'fake_phases':phases})
        core.save(root/'unit-results.json',tested)
        # Prove unchanged production primitives rather than rerunning old transport matrix.
        old=P.parents[1]/'20261023/direct-api-v1'
        def fun(source,name):return ast.dump(next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name==name),include_attributes=False)
        checks['transport_unchanged']=(P/'transport.py').read_bytes()==(old/'transport.py').read_bytes()
        for name in ['extract','clean_env','bounded_process']:checks[name+'_unchanged']=fun((P/'core.py').read_text(),name)==fun((old/'core.py').read_text(),name)
        checks['usage_unchanged']=fun((P/'usage.py').read_text(),'usage_record')==fun((old/'usage.py').read_text(),'usage_record')
        checks['calibration_core_unchanged']=core.sha(P/'core.py')==core.read(P/'development/calibration-source-lock.json')['core.py']
    except BaseException as e:
        checks['exception']=type(e).__name__;core.save_bytes(root/'exception.txt',traceback.format_exc().encode())
    finally:
        server.shutdown();core.save(root/'http-records.json',{'counts':dict(counts),'records':records});summary={'utc':core.utc(),'passed':bool(checks) and all(x is True for x in checks.values()),'checks':checks,'posts':sum(counts.values()),'external_model_calls':0,'real_credentials_read':False,'eda_calls':0,'source_lock_sha256':core.sha(P/'source-lock.json')};core.save(root/'summary.json',summary);print(json.dumps(summary),flush=True)
    return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
