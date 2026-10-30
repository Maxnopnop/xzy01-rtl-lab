"""Pure mock of the frozen transport's explicit CONNECT branch. No sockets."""
import hashlib,importlib.util,json,socket
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1]
F=R/'exploration/20261024/public-rag-next-executor-v1/transport.py'
spec=importlib.util.spec_from_file_location('t',F);t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
raw=b'{"messages":[]}';events=[]
class Response:
 status=200
 def read(self,n):return b'{}'
 def getheader(self,k):return '2'
class Connection:
 fail=False
 def __init__(self,host,port,**kw):
  events.append(('connect',host,port));assert (host,port)==('127.0.0.1',3213)
 def set_tunnel(self,host,port):events.append(('tunnel',host,port));assert (host,port)==('openrouter.ai',443)
 def request(self,method,target,body,headers):
  events.append(('request',method,target));assert method=='POST' and target=='/api/v1/chat/completions' and body==raw
  if self.fail:raise ConnectionRefusedError('offline')
 def getresponse(self):return Response()
 def close(self):pass
def deny(*a,**k):raise AssertionError('Real sockets prohibited')
route={'endpoint':'https://openrouter.ai/api/v1/chat/completions','proxy_url':'http://127.0.0.1:3213'}
rows=[]
with patch.object(socket.socket,'connect',deny),patch.object(t.http.client,'HTTPSConnection',Connection):
 for code,want in [(200,'HTTP_OK'),(302,'REDIRECT_REJECTED'),(403,'HTTP_ERROR'),(429,'HTTP_ERROR'),(500,'HTTP_ERROR')]:
  events.clear();Response.status=code
  e=t.send_once(raw,route,'FAKE_OFFLINE_KEY',180)
  assert e['outcome']==want and sum(v[0]=='connect' for v in events)==1 and sum(v[0]=='request' for v in events)==1
  rows.append({'http':code,'outcome':want,'events':list(events)})
 events.clear();Connection.fail=True
 e=t.send_once(raw,route,'FAKE_OFFLINE_KEY',180)
 assert e['outcome']=='UNKNOWN' and sum(v[0]=='connect' for v in events)==1
 rows.append({'case':'proxy_connection_failure','outcome':e['outcome'],'events':events.copy()})
out={'passed':True,'cases':rows,'transport_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'network_calls':0,'model_calls':0,'claim':'Explicit proxy target and CONNECT target; one POST attempt; no direct fallback or retry.'}
(P/'connect-audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'cases':len(rows),'network_calls':0}))
