"""Real loopback HTTP audit. Never opens an external endpoint or reads API keys."""
import collections,http.server,json,pathlib,socket,threading,time,traceback
from urllib.parse import urlsplit
import core,dispatcher,transport

R=pathlib.Path(__file__).resolve().parent
MODES=['400','401','403','429','timeout','interrupted','redirect','success','missing_usage']

def main():
    out=R/'mock-v1';out.mkdir(exist_ok=False)
    core.save(out/'predeclared-plan.json',{'matrix':{'models':core.MODELS,'modes':MODES,'slots':27},'complete_input_http_captures':120,'proxy_cases':2,'worker_timeout':.25,'observation':'Allow worker to exit or parent hard guard; then re-enter ledger and compare POST counts. No harness retry. Timeout waits1s for server cleanup.','cap_and_order':'240 synthetic ledger reservations, no network','real_api_requests':0,'real_model_calls':0,'synthetic_bearer':'OFFLINE_SYNTHETIC_TOKEN_ONLY','fixture_provider':'MOCK_ONLY_NOT_A_CATALOG_CLAIM'})
    counts=collections.Counter();records=[];modes={};lock=threading.Lock()
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_CONNECT(self):
            with lock:counts['CONNECT']+=1;records.append({'method':'CONNECT','target':self.path,'authorization_present':bool(self.headers.get('Authorization'))})
            self.send_response(407);self.send_header('Content-Length','0');self.end_headers()
        def do_POST(self):
            path=urlsplit(self.path).path;tag=path.split('/')[1]
            raw=self.rfile.read(int(self.headers['Content-Length']))
            with lock:
                counts[tag]+=1;number=counts[tag];records.append({'method':'POST','tag':tag,'target':self.path,'sha256':core.digest(raw),'authorization_is_synthetic':self.headers.get('Authorization')=='Bearer OFFLINE_SYNTHETIC_TOKEN_ONLY'})
            folder=out/'captured'/tag;folder.mkdir(parents=True,exist_ok=True)
            core.save_bytes(folder/f'{number}.bin',raw)
            mode=modes.get(tag,'success');obj=json.loads(raw)
            if mode=='timeout':time.sleep(1);self.close_connection=True;return
            if mode=='interrupted':
                self.send_response(200);self.send_header('Content-Length','10000');self.end_headers();self.wfile.write(b'{"partial":');self.wfile.flush();self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            if mode=='redirect':
                self.send_response(307);self.send_header('Location',f'http://127.0.0.1:{self.server.server_address[1]}/redirect_target/chat/completions');self.send_header('Content-Length','0');self.end_headers();return
            if mode.isdigit():
                body=b'{"error":{"message":"fixture"}}';self.send_response(int(mode))
            else:
                response={'id':'offline-fixture','model':obj['model'],'provider':'MockProvider','choices':[{'message':{'role':'assistant','content':'module TopModule; endmodule'},'finish_reason':'stop'}]}
                if mode!='missing_usage':response['usage']={'prompt_tokens':10,'completion_tokens':9000,'total_tokens':9010,'prompt_tokens_details':{'cached_tokens':0},'completion_tokens_details':{'reasoning_tokens':7}}
                body=json.dumps(response).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();port=server.server_address[1]
    base={'endpoint':f'http://127.0.0.1:{port}/default/chat/completions','api_key_env':'MOCK_UNUSED','proxy_url':None,'proxy_env':None,'provider_only':['mock-only'],'expected_provider':'MockProvider'}
    slots=dispatcher.prepare_slots(base)
    core.save(out/'source-at-test.json',core.read(R/'source-lock.json'))
    results=[];checks={}
    def fake_judge(*args):return {'status':'MOCK_JUDGE_NOT_EDA','stage':'offline_fixture','stop':False}
    try:
        for model in core.MODELS:
            slot=next(s for s in slots if s['model']==model)
            for mode in MODES:
                tag=model+'-'+mode;modes[tag]=mode;route=dict(base,endpoint=f'http://127.0.0.1:{port}/{tag}/chat/completions')
                routefile=out/(tag+'-route.json');core.save(routefile,route);root=out/'runs'/tag
                call=lambda s,f,t:dispatcher.live_transport(s,f,.25,routefile,True)
                first=dispatcher.execute(root,[slot],'MOCK',call,fake_judge)
                if mode=='timeout':time.sleep(1.05)
                before=counts[tag];second=dispatcher.execute(root,[slot],'MOCK',call,fake_judge)
                result=core.read(root/'results'/f"{slot['id']}.json")
                expected='MOCK_JUDGE_NOT_EDA' if mode in ['success','missing_usage'] else 'UNKNOWN' if mode in ['timeout','interrupted'] else 'SERVICE_ERROR'
                passed=before==counts[tag]==1 and result['status']==expected and first['reserved']==second['reserved']==1
                if mode=='missing_usage':passed=passed and all(v is None for v in result['usage_normalized']['values'].values())
                entry={'model':model,'mode':mode,'post_count':counts[tag],'resume_additional_posts':counts[tag]-before,'status':result['status'],'expected':expected,'pass':passed};results.append(entry);print(json.dumps(entry),flush=True)
        checks['no_redirect_target_post']=counts['redirect_target']==0
        # Every task/condition exactly once per model, using frozen sample1; local captures only.
        groups={}
        for slot in [s for s in slots if s['sample']==1]:
            tag='full-'+str(slot['ordinal']);modes[tag]='success';folder=out/'full'/tag;folder.mkdir(parents=True)
            core.save_bytes(folder/'request.json',slot['wire_bytes']);route=dict(base,endpoint=f'http://127.0.0.1:{port}/{tag}/chat/completions');rf=folder/'route-input.json';core.save(rf,route)
            envelope=dispatcher.live_transport(slot,folder,2,rf,True)
            assert envelope['outcome']=='HTTP_OK' and counts[tag]==1
            captured=(out/'captured'/tag/'1.bin').read_bytes();assert captured==slot['wire_bytes']
            obj=json.loads(captured);wire_model=obj.pop('model')
            groups.setdefault((slot['task'],slot['condition']),[]).append({'model':wire_model,'body_without_model':obj})
        comparisons=[]
        for (task,condition),values in groups.items():
            equal=len(values)==3 and all(v['body_without_model']==values[0]['body_without_model'] for v in values)
            comparisons.append({'task':task,'condition':condition,'models':[v['model'] for v in values],'equal_except_model':equal})
        core.save(out/'full-request-diff.json',{'normalization':'Separate only top-level model. No content/roles/parameters removed. HTTP Authorization is identical synthetic test token.','groups':comparisons})
        checks['40_groups_equal']=len(comparisons)==40 and all(x['equal_except_model'] for x in comparisons)
        # An explicit proxy receives the request instead of origin (no actual forwarding needed).
        folder=out/'proxy';folder.mkdir();slot=slots[0];core.save_bytes(folder/'request.json',slot['wire_bytes'])
        route=dict(base,endpoint='http://127.0.0.1:1/proxy_check/chat/completions',proxy_url=f'http://127.0.0.1:{port}');rf=folder/'route-input.json';core.save(rf,route)
        env=dispatcher.live_transport(slot,folder,2,rf,True)
        checks['explicit_proxy_crosses_child_boundary']=env['outcome']=='HTTP_OK' and counts['proxy_check']==1
        before=counts['CONNECT'];env=transport.send_once(slot['wire_bytes'],{'endpoint':'https://example.invalid/v1/chat/completions','proxy_url':f'http://127.0.0.1:{port}'},'OFFLINE_SYNTHETIC_TOKEN_ONLY',1)
        core.save(out/'https-connect-rejected.json',env)
        checks['https_proxy_connect_once_no_retry']=counts['CONNECT']==before+1 and env['outcome']=='UNKNOWN'
        # Crash reservation without any response: recovery must not invoke transport.
        rr=out/'reserved-crash';ledger=core.Ledger(rr,[slots[0]],'MOCK');ledger.reserve(slots[0],slots[0]['request_sha256'])
        calls=[];recovered=dispatcher.execute(rr,[slots[0]],'MOCK',lambda *args:calls.append(1),fake_judge)
        checks['unfinished_reservation_not_resent']=not calls and recovered['unknown']==1 and recovered['stopped']
        # Fixed order and total ceiling, entirely synthetic ledger operations.
        ledger=core.Ledger(out/'cap-ledger',slots,'MOCK');rejected=False
        try:ledger.reserve(slots[1],slots[1]['request_sha256'])
        except AssertionError:rejected=True
        checks['out_of_order_rejected']=rejected
        for s in slots:
            ledger.reserve(s,s['request_sha256']);ledger.finish(s,{'status':'OFFLINE_LEDGER_FIXTURE','complete_http_return':False,'usage':None})
        rejected=False
        try:ledger.reserve(slots[0],slots[0]['request_sha256'])
        except AssertionError:rejected=True
        checks['240_ceiling_enforced']=len(ledger.reservations())==240 and rejected
    except BaseException as e:
        checks['audit_exception']=type(e).__name__;core.save_bytes(out/'exception.txt',traceback.format_exc().encode())
    finally:
        server.shutdown();core.save(out/'http-observation.json',{'counts':dict(counts),'requests':records})
        summary={'matrix':results,'checks':checks,'passed':len(results)==27 and all(x['pass'] for x in results) and bool(checks) and all(v is True for v in checks.values()),'real_model_calls':0,'formal_reservations':0,'model_permissions':'NOT_TESTED','server_internal_retry':'UNOBSERVABLE'}
        core.save(out/'summary.json',summary);print(json.dumps(summary),flush=True)
    return 0 if summary['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
