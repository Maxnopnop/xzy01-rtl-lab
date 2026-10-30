"""Exactly one official-style Chat Completions POST. No login-token access/retry."""
import hashlib,json,os,sys,urllib.request,urllib.error
from pathlib import Path
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def main():
 request,route,result,timeout=sys.argv[1:];raw=Path(request).read_bytes();cfg=json.loads(Path(route).read_bytes());secret=os.environ.get('RTL_RAG_SECRET','');envelope={'request_sha256':hashlib.sha256(raw).hexdigest()}
 if not secret:envelope.update(outcome='LOCAL_CONFIG_ERROR')
 else:
  req=urllib.request.Request(cfg['endpoint'],data=raw,headers={'Content-Type':'application/json','Accept':'application/json','Authorization':'Bearer '+secret},method='POST')
  try:
   # No SDK retry, redirects disabled. Parent enforces wall timeout too.
   with urllib.request.build_opener(NoRedirect()).open(req,timeout=float(timeout)) as r:
    body=r.read(1048577);envelope['http_status']=r.status
   envelope['response_bytes']=len(body);envelope['raw_body_sha256']=hashlib.sha256(body).hexdigest()
   if len(body)>1048576:envelope.update(outcome='RESPONSE_SIZE_LIMIT')
   else:
    text=body.decode('utf-8')
    if secret in text or json.dumps(secret)[1:-1] in text:envelope.update(outcome='SECRET_ECHO_REDACTED')
    else:envelope.update(outcome='HTTP_OK',body=text)
  except urllib.error.HTTPError as e:envelope.update(outcome='HTTP_ERROR',http_status=e.code)
  except Exception as e:envelope.update(outcome='UNKNOWN',error_type=type(e).__name__)
 with Path(result).open('xb') as f:f.write((json.dumps(envelope,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
 return 0
if __name__=='__main__':raise SystemExit(main())
