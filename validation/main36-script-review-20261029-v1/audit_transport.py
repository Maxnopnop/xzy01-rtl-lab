"""No sockets: exercise frozen HTTP transport with an injected connection."""
import hashlib, importlib.util, json, socket
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1]
N=R/'exploration/20261029/main36-script-newbatch-v1'
spec=importlib.util.spec_from_file_location('audited_transport',N/'reuse/transport.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
def deny(*a,**k):raise AssertionError('No real network allowed')
raw=b'{"messages":[{"role":"user","content":"OFFLINE"}]}'
events=[]
class Response:
 status=200
 def read(self,n):return b'{}'
 def getheader(self,k):return '2'
class Connection:
 def __init__(self,*a,**k):pass
 def request(self,method,target,body,headers):
  events.append((method,target,body));assert body==raw
 def getresponse(self):return Response()
 def close(self):pass
rows=[]
with patch.object(socket.socket,'connect',deny),patch.object(t.http.client,'HTTPSConnection',Connection):
 for code,want in [(200,'HTTP_OK'),(302,'REDIRECT_REJECTED'),(403,'HTTP_ERROR'),(429,'HTTP_ERROR'),(500,'HTTP_ERROR')]:
  Response.status=code;events.clear()
  out=t.send_once(raw,{'endpoint':'https://openrouter.ai/api/v1/chat/completions','proxy_url':None},'fake-review-key',180)
  assert out['outcome']==want and len(events)==1 and events[0][0]=='POST'
  assert out['request_sha256']==hashlib.sha256(raw).hexdigest()
  rows.append({'status':code,'verdict':want,'post_invocations':len(events)})
out={'passed':True,'cases':rows,'network_requests':0,'model_calls':0,'transport_sha256':hashlib.sha256((N/'reuse/transport.py').read_bytes()).hexdigest()}
(P/'transport-audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
