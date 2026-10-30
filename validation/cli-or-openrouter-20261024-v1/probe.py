import json, pathlib, hashlib, os, subprocess, tempfile, threading, http.server, socket, time, tomllib

R=pathlib.Path(__file__).resolve().parent
B=R.parents[1]
P=B/'exploration/20261023/public-rag-all20-v1'
MODELS=['gpt-5.6-luna']  # one local-only entry check; not a three-model certification
EXE=pathlib.Path('C:/Users/A/AppData/Roaming/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 out=R/'local-tests-candidate2';out.mkdir(exist_ok=False)
 w=pathlib.Path(tempfile.mkdtemp(prefix='xzy-cache-repaired-'))
 home=w/'home';home.mkdir();cwd=w/'work';cwd.mkdir()
 msgs=json.loads((P/'messages/Prob023_vector100r__no_rag.json').read_text(encoding='utf-8'))
 inst=cwd/'system.txt';inst.write_bytes(msgs[0]['content'].encode('utf-8'))
 active={'path':None,'mode':'400','posts':0,'denials':[]}
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args): pass
  def do_CONNECT(self):
   active['denials'].append({'method':'CONNECT','path':self.path});self.send_error(403,'LOCAL_DENY')
  def do_GET(self):
   active['denials'].append({'method':'GET','path':self.path});self.send_error(400,'LOCAL_DENY')
  def do_POST(self):
   if self.path!='/v1/responses':
    active['denials'].append({'method':'POST','path':self.path});self.send_error(400,'LOCAL_DENY');return
   active['posts']+=1;n=active['posts'];p=active['path']
   size=int(self.headers.get('Content-Length','0'))
   if size>1048576:self.send_error(413);return
   body=self.rfile.read(size)
   (p/f'request-{n}.bin').write_bytes(body)
   save(p/f'headers-{n}.json',dict(self.headers))
   mode=active['mode']
   if mode=='disconnect':
    self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
   if mode=='sse_disconnect':
    self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
    self.wfile.write(b'event: response.created\ndata: {"type":"response.created","response":{"id":"offline_mock","status":"in_progress"}}\n\n');self.wfile.flush()
    self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
   self.send_response(int(mode));self.send_header('Content-Type','application/json');self.end_headers()
   self.wfile.write(b'{"error":{"message":"OFFLINE_FIXTURE_ONLY","type":"invalid_request_error"}}')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);port=server.server_address[1]
 threading.Thread(target=server.serve_forever,daemon=True).start()
 config=f'''chatgpt_base_url = "http://127.0.0.1:{port}/blocked-chatgpt/"
model_provider = "offline_audit"
model_catalog_json = {json.dumps((R/'bundled-catalog.json').as_posix())}
model_instructions_file = {json.dumps(inst.as_posix())}
check_for_update_on_startup = false
cli_auth_credentials_store = "file"
agents.enabled = false
project_doc_max_bytes = 0
web_search = "disabled"
[features]
shell_tool = false
remote_plugin = false
[tools]
view_image = false
[apps._default]
enabled = false
[model_providers.offline_audit]
name = "Local audit only"
base_url = "http://127.0.0.1:{port}/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
'''
 (home/'config.toml').write_text(config,encoding='utf-8');(out/'config.toml').write_text(config,encoding='utf-8')
 env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATH','TEMP','TMP','PATHEXT','SYSTEMDRIVE','PROCESSOR_ARCHITECTURE']}
 env.update({'CODEX_HOME':str(home),'HOME':str(home),'USERPROFILE':str(home),'HTTP_PROXY':f'http://127.0.0.1:{port}','HTTPS_PROXY':f'http://127.0.0.1:{port}','ALL_PROXY':f'http://127.0.0.1:{port}','NO_PROXY':'127.0.0.1,localhost'})
 save(out/'predeclared-plan.json',{'binary':str(EXE),'binary_sha256':sha(EXE),'catalog_sha256':sha(R/'bundled-catalog.json'),'source_asset_sha256':sha(P/'messages/Prob023_vector100r__no_rag.json'),'system_sha256':sha(inst),'candidate':2,'candidate_probe_cap':1,'retry_test_extra_cap':0,'retry_modes':['400 entry check only; zero-retry production test NOT_EXECUTED'],'max_seconds_each':20,'max_posts_per_launch_guard':2,'real_generation_calls':0,'cwd':str(cwd),'environment':env,'limits':'Custom-provider local mock, not production login. All configured network endpoints loopback plus rejecting proxy; no OS firewall claim. Stop new tests on any denied external attempt/cache parse failure/timeout. No harness retry. All outputs retained.'})
 results=[]
 def run(tag,model,mode):
  p=out/tag;p.mkdir();active.update(path=p,mode=mode,posts=0,denials=[])
  args=[str(EXE),'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','-C',str(cwd),'-m',model,'-s','read-only','--json',msgs[1]['content']]
  settings=tomllib.loads(config)
  def overrides(obj,prefix=''):
   result=[]
   for key,value in obj.items():
    field=(prefix+'.' if prefix else '')+key
    if isinstance(value,dict):result+=overrides(value,field)
    else:result += ['-c',field+'='+json.dumps(value)]
   return result
  args[-1:-1]=overrides(settings)
  save(p/'command.json',args)
  started=time.monotonic();reason=None
  with (p/'stdout.txt').open('wb') as so,(p/'stderr.txt').open('wb') as se:
   proc=subprocess.Popen(args,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
   while proc.poll() is None:
    if active['denials']:reason='DENIED_EXTERNAL_ATTEMPT'
    elif active['posts']>2:reason='RETRY_GUARD'
    elif time.monotonic()-started>20:reason='TIMEOUT'
    if reason:
     subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True);proc.wait();break
    time.sleep(.05)
  rec={'tag':tag,'model':model,'mode':mode,'exit_code':proc.returncode,'posts':active['posts'],'denied_external':list(active['denials']),'stop_reason':reason,'seconds':round(time.monotonic()-started,3),'cache_error':'failed to load models cache' in (p/'stderr.txt').read_text(encoding='utf-8',errors='replace')}
  save(p/'receipt.json',rec);results.append(rec);save(out/'receipts.json',results);print(json.dumps(rec),flush=True)
  return not (reason or rec['cache_error'] or rec['denied_external'])
 try:
  for model in MODELS:
   if not run('probe-'+model,model,'400'):return
  for mode in []:  # no extra launches in this bounded recheck
   if not run('failure-'+mode,MODELS[0],mode):return
 finally:
  server.shutdown()
  save(out/'final-counts.json',{'launches':len(results),'posts':sum(x['posts'] for x in results),'real_model_calls':0,'formal_slots_reserved':0,'denied_external':sum(len(x['denied_external']) for x in results)})

if __name__=='__main__':main()
