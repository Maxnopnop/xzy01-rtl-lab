import pathlib,json,hashlib,os,subprocess,tempfile,threading,http.server,shutil
R=pathlib.Path(__file__).resolve().parent
B=R.parents[2]
P=B/'exploration/20261023/public-rag-all20-v1'
def save(n,v): (R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
exe=pathlib.Path('C:/Users/A/AppData/Roaming/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe')
w=pathlib.Path(tempfile.mkdtemp(prefix='xzy-mock-request-'));home=w/'home';home.mkdir();work=w/'work';work.mkdir()
m=json.loads((P/'messages/Prob023_vector100r__no_rag.json').read_text(encoding='utf-8'))
inst=work/'system.txt';inst.write_bytes(m[0]['content'].encode('utf-8'))
shutil.copyfile(B/'exploration/20261023/cli-fairness-offline-v1/isolated-home/models_cache.json',home/'models_cache.json')
current='none';counts={};external=[]
class Sink(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def do_CONNECT(self):
  external.append({'method':'CONNECT','target':self.path});self.send_error(403,'offline deny')
 def do_GET(self):
  external.append({'method':'GET','target':self.path});self.send_error(400,'offline deny')
 def do_POST(self):
  n=counts.get(current,0)+1;counts[current]=n
  body=self.rfile.read(int(self.headers.get('Content-Length','0')))
  (R/f'{current}-request-{n}.bin').write_bytes(body)
  save(f'{current}-headers-{n}.json',{'path':self.path,'headers':dict(self.headers)})
  self.send_response(400);self.send_header('Content-Type','application/json');self.end_headers()
  self.wfile.write(b'{"error":{"message":"OFFLINE_CAPTURE_ONLY","type":"invalid_request_error"}}')
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Sink);port=server.server_address[1]
threading.Thread(target=server.serve_forever,daemon=True).start()
config=f'''model_provider = "offline_capture"
agents.enabled = false
project_doc_max_bytes = 0
web_search = "disabled"
model_instructions_file = {json.dumps(inst.as_posix())}
[features]
shell_tool = false
[tools]
view_image = false
[model_providers.offline_capture]
name = "Local capture only"
base_url = "http://127.0.0.1:{port}/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
'''
(home/'config.toml').write_text(config,encoding='utf-8');(R/'candidate.toml').write_text(config,encoding='utf-8')
env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATH','TEMP','TMP','PATHEXT','SYSTEMDRIVE','PROCESSOR_ARCHITECTURE']}
env.update({'CODEX_HOME':str(home),'HOME':str(home),'USERPROFILE':str(home),'HTTP_PROXY':f'http://127.0.0.1:{port}','HTTPS_PROXY':f'http://127.0.0.1:{port}','ALL_PROXY':f'http://127.0.0.1:{port}','NO_PROXY':'127.0.0.1,localhost'})
save('plan.json',{'binary':str(exe),'binary_sha256':sha(exe),'max_candidates':2,'candidates_used':1,'max_probe_processes':3,'max_seconds_each':25,'scope':'Loopback custom Responses provider; capture then return400. No inference server, auth copied/read or retry.','network':'Configured endpoint loopback; credential-free allowlist environment; external proxy denies traffic; not OS firewall isolation.','cwd':str(work),'environment':env,'system_sha256':sha(inst),'gate_120':'Only if full visible request equal apart from model/nonsemantic IDs; mock remains distinct from production'})
results=[]
for current in ['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol']:
 args=[str(exe),'exec','--ephemeral','--skip-git-repo-check','-C',str(work),'-m',current,'-s','read-only','--json',m[1]['content']]
 save(current+'-command.json',args)
 try:
  x=subprocess.run(args,cwd=work,env=env,capture_output=True,timeout=25);code=x.returncode;out=x.stdout;err=x.stderr
 except subprocess.TimeoutExpired as e: code='TIMEOUT';out=e.stdout or b'';err=e.stderr or b''
 (R/(current+'-stdout.txt')).write_bytes(out);(R/(current+'-stderr.txt')).write_bytes(err)
 results.append({'model':current,'exit_code':code,'captured':counts.get(current,0)})
 if code=='TIMEOUT' or counts.get(current,0)!=1 or external: break
server.shutdown();save('receipts.json',results);save('denied-external-attempts.json',external)
print(json.dumps(results));print(json.dumps(external))
