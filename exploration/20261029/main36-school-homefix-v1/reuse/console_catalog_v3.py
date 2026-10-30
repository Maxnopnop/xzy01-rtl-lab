"""Public, unauthenticated metadata GET only; never probes inference availability."""
import datetime
import hashlib
import http.client
import json
from pathlib import Path
import re

def snapshot(model, destination):
    if model is not None and not re.fullmatch(r'[a-z0-9_-]+/[A-Za-z0-9_.:-]+', model):
        raise ValueError('Exact model ID required')
    path='/api/v1/models'+('/'+model+'/endpoints' if model else '')
    conn=http.client.HTTPSConnection('openrouter.ai',timeout=30)
    try:
        conn.request('GET',path,headers={'Accept':'application/json'})
        response=conn.getresponse();raw=response.read(16*1024*1024+1)
        if response.status!=200 or len(raw)>16*1024*1024:raise ValueError('Metadata GET failed; no retry')
        json.loads(raw)
    finally:conn.close()
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    (destination/'response.json').write_bytes(raw)
    meta=dict(source_url='https://openrouter.ai'+path,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(raw).hexdigest(),method='GET',authenticated=False,inference_availability='NOT_VERIFIED')
    (destination/'source.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta

def profiles(package):
    """Validate declarations against hash-locked endpoint metadata; no rewriting."""
    from console_bridge_v3 import require,read,inside,sha,canonical
    data=package.data;lock=data['files'];items=data.get('models')
    require(isinstance(items,list) and items,'Declare exact model set')
    out={}
    for p in items:
        mid=p['id'];require(isinstance(mid,str) and re.fullmatch(r'[a-z0-9_-]+/[A-Za-z0-9_.:-]+',mid),'Invalid model ID')
        require(mid not in out,'Duplicate model ID')
        require(p['author_namespace']==mid.split('/')[0],'Author namespace mismatch')
        for n in ('endpoint_metadata','metadata_source'):
            require(p[n] in lock,'Metadata not frozen')
        meta=read(inside(package.base,p['metadata_source']))
        require(meta['source_url']=='https://openrouter.ai/api/v1/models/'+mid+'/endpoints' and meta['method']=='GET' and meta['authenticated'] is False,'Metadata source mismatch')
        require(isinstance(meta.get('retrieved_utc'),str) and meta['retrieved_utc'],'Missing metadata time')
        require(meta['sha256']==sha(inside(package.base,p['endpoint_metadata'])),'Metadata binding mismatch')
        catalogue=read(inside(package.base,p['endpoint_metadata']))['data']
        require(catalogue['id']==mid,'Metadata model mismatch')
        endpoints=[e for e in catalogue['endpoints'] if e.get('tag')==p['provider_tag'] and e.get('provider_name')==p['response_provider']]
        require(len(endpoints)==1,'Exact endpoint tag/name not unique in metadata')
        endpoint=endpoints[0]
        require(endpoint.get('status')==0,'Endpoint metadata not active')
        require(isinstance(p['parameters'],dict),'Parameters must be explicit object')
        allowed={'temperature','top_p','top_k','min_p','top_a','seed','reasoning','max_tokens','max_completion_tokens','frequency_penalty','presence_penalty','repetition_penalty'}
        require(set(p['parameters'])<=allowed,'Unsupported request control; refuse silently adding fields')
        require(set(p['parameters'])<=set(endpoint['supported_parameters']),'Parameter unsupported by selected endpoint')
        # Exact values are frozen and reviewed. Do not normalize provider-specific reasoning.
        require(isinstance(p.get('comparison_note'),str) and p['comparison_note'].strip(),'Declare sampling/reasoning comparability limitations')
        out[mid]=p
    return out

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--model');a.add_argument('--output',required=True)
    args=a.parse_args();print(json.dumps(snapshot(args.model,args.output),indent=2))
