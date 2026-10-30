"""Single http.client request; no SDK, redirects, retries, CLI or fallback."""
import hashlib, http.client, json, os, re, ssl, sys
from pathlib import Path
from urllib.parse import urlsplit

LIMIT=1048576

def route_values(cfg, environ, local_mock=False):
    if set(cfg) != {'endpoint','api_key_env','proxy_url','proxy_env','provider_only','expected_provider'}:
        raise ValueError('Unexpected route fields')
    endpoint=cfg['endpoint'];u=urlsplit(endpoint)
    if u.username or u.password or u.query or u.fragment or not u.hostname:
        raise ValueError('Endpoint must have no credentials/query/fragment')
    if not u.path.endswith('/chat/completions'):
        raise ValueError('Chat Completions endpoint required')
    if local_mock:
        if u.scheme!='http' or u.hostname!='127.0.0.1': raise ValueError('Mock requires literal loopback HTTP')
    elif u.scheme!='https': raise ValueError('Live endpoint requires HTTPS')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',cfg['api_key_env']):
        raise ValueError('Invalid API credential environment name')
    if cfg['proxy_url'] is not None and cfg['proxy_env'] is not None:
        raise ValueError('Use one proxy source')
    proxy=cfg['proxy_url']
    if cfg['proxy_env'] is not None:
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',cfg['proxy_env']): raise ValueError('Invalid proxy env name')
        proxy=environ.get(cfg['proxy_env'])
        if not proxy: raise ValueError('Configured proxy environment variable absent')
    if proxy is not None:
        v=urlsplit(proxy)
        if v.scheme!='http' or not v.hostname or v.username or v.password or v.query or v.fragment or v.path not in ('','/'):
            raise ValueError('Proxy must be an HTTP CONNECT proxy URL without embedded credentials')
        if local_mock and v.hostname!='127.0.0.1': raise ValueError('Mock proxy must be loopback')
        if v.port is None: raise ValueError('Explicit proxy port required')
    return {'endpoint':endpoint,'proxy_url':proxy}

def send_once(raw, route, secret, timeout):
    envelope={'request_sha256':hashlib.sha256(raw).hexdigest(),'client_post_invocations':0}
    conn=None
    try:
        if not secret: return dict(envelope,outcome='LOCAL_CONFIG_ERROR')
        u=urlsplit(route['endpoint']);proxy=route.get('proxy_url');target=u.path
        if proxy:
            v=urlsplit(proxy)
            if u.scheme=='https':
                conn=http.client.HTTPSConnection(v.hostname,v.port,timeout=timeout,context=ssl.create_default_context())
                conn.set_tunnel(u.hostname,u.port or 443)
            else:
                conn=http.client.HTTPConnection(v.hostname,v.port,timeout=timeout);target=route['endpoint']
        elif u.scheme=='https':
            conn=http.client.HTTPSConnection(u.hostname,u.port or 443,timeout=timeout,context=ssl.create_default_context())
        else: conn=http.client.HTTPConnection(u.hostname,u.port or 80,timeout=timeout)
        envelope['client_post_invocations']=1
        conn.request('POST',target,body=raw,headers={'Content-Type':'application/json','Accept':'application/json','Authorization':'Bearer '+secret,'Connection':'close'})
        response=conn.getresponse();envelope['http_status']=response.status
        body=response.read(LIMIT+1)
        envelope['response_bytes']=len(body);envelope['raw_body_sha256']=hashlib.sha256(body).hexdigest()
        if len(body)>LIMIT: return dict(envelope,outcome='RESPONSE_SIZE_LIMIT')
        declared=response.getheader('Content-Length')
        if declared is not None and int(declared)!=len(body): return dict(envelope,outcome='UNKNOWN',error_type='IncompleteBody')
        text=body.decode('utf-8')
        if secret in text or json.dumps(secret)[1:-1] in text:
            return dict(envelope,outcome='SECRET_ECHO_REDACTED')
        envelope['body']=text
        if 300<=response.status<400:return dict(envelope,outcome='REDIRECT_REJECTED')
        if not 200<=response.status<300:return dict(envelope,outcome='HTTP_ERROR')
        return dict(envelope,outcome='HTTP_OK')
    except Exception as e:
        return dict(envelope,outcome='UNKNOWN',error_type=type(e).__name__)
    finally:
        if conn:conn.close()

def main():
    request,route,result,timeout=sys.argv[1:]
    raw=Path(request).read_bytes();cfg=json.loads(Path(route).read_bytes())
    # Parent validates live/mock route and resolves explicit proxy; no ambient proxy discovery.
    env=send_once(raw,cfg,os.environ.get('RTL_RAG_SECRET',''),float(timeout))
    with Path(result).open('xb') as f:
        f.write(json.dumps(env,ensure_ascii=False,indent=2).encode('utf-8'));f.flush();os.fsync(f.fileno())

if __name__=='__main__':main()
