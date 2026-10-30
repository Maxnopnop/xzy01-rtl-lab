"""Frozen metadata selection and one-shot public source fetching, only after A seal."""
import datetime,hashlib,json,re,sys,urllib.request
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parent;B=ROOT/'B'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def verify_a():
    seal=read(ROOT/'A-seal.json');assert sha(ROOT/'A-lock.json')==seal['a_lock_sha256']
    lock=read(ROOT/'A-lock.json')
    assert set(lock)=={p.relative_to(A).as_posix() for p in A.rglob('*') if p.is_file()}
    for path,h in lock.items():assert sha(A/path)==h,path
    return seal
def select():
    seal=verify_a();assert not B.exists(),'No B reselection or overwrite'
    B.mkdir();write(B/'start.json',{'utc':utc(),'client_date':'2026-10-23','a_lock_sha256':seal['a_lock_sha256'],
        'a_frozen_utc':seal['frozen_utc'],'new_content_reads_so_far':0,'model_calls':0,'eda_calls':0})
    policy=read(A/'selection-policy.json');ex=read(A/'exclusions.json')
    paths={x['path']:x for x in read(A/'metadata/tree.json')['tree'] if x['type']=='blob'}
    ids=sorted(p.removeprefix('dataset_spec-to-rtl/').removesuffix('_prompt.txt') for p in paths
        if p.startswith('dataset_spec-to-rtl/') and p.endswith('_prompt.txt'))
    excluded=[];eligible=[]
    for task in ids:
        reason='EXPLICIT_PREVIOUSLY_EXPOSED' if task in ex['explicit_public_ids'] else (
            'CONSERVATIVE_HISTORY_FAMILY_METADATA' if re.search(ex['conservative_metadata_family_regex'],task,re.I) else None)
        if reason:excluded.append({'id':task,'reason':reason})
        else:eligible.append(task)
    key=lambda t:(hashlib.sha256((policy['seed']+'\n'+t).encode()).hexdigest(),t)
    ordered=sorted(eligible,key=key)
    chosen=[{'rank':i+1,'id':t,'order_sha256':key(t)[0],
       'files':{s:dict(path=f'dataset_spec-to-rtl/{t}_{s}',git_blob_sha1=paths.get(f'dataset_spec-to-rtl/{t}_{s}',{}).get('sha'))
                for s in ('prompt.txt','ref.sv','test.sv')}} for i,t in enumerate(ordered[:policy['max_new_candidates']])]
    write(B/'candidate-order.json',{'utc':utc(),'a_lock_sha256':seal['a_lock_sha256'],
        'dataset_commit':policy['commit'],'metadata_total_ids':len(ids),'metadata_exclusions':excluded,
        'remaining_ordered_ids':ordered,'new_candidates':chosen,'new_content_reads_so_far':0})
    print(json.dumps({'candidate_ids':[r['id'] for r in chosen],'metadata_excluded':len(excluded),'a_lock_sha256':seal['a_lock_sha256']}))
def fetch():
    seal=verify_a();assert not (B/'access.json').exists(),'No fetch rerun; preserve unknown/failed attempts'
    inventory=read(B/'candidate-order.json');assert inventory['a_lock_sha256']==seal['a_lock_sha256']
    policy=read(A/'selection-policy.json');visits=[];total=0
    write(B/'fetch-start.json',{'utc':utc(),'a_lock_sha256':seal['a_lock_sha256'],
                               'candidate_order_sha256':sha(B/'candidate-order.json')})
    for task in inventory['new_candidates']:
        for kind,info in task['files'].items():
            path=info['path'];url=f'https://raw.githubusercontent.com/NVlabs/verilog-eval/{policy["commit"]}/{path}'
            assert len(visits)<policy['http_max_requests'] and url not in {v['url'] for v in visits}
            row={'utc':utc(),'task':task['id'],'kind':kind,'url':url,'local':'originals/'+path,'git_blob_expected':info['git_blob_sha1']}
            visits.append(row);write(B/'access.json',visits)
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'fixed-public-rag-static-preparation'})
                with urllib.request.urlopen(req,timeout=policy['timeout_seconds']) as r:
                    raw=r.read(policy['raw_file_limit_bytes']+1);row['http_status']=r.status
                assert len(raw)<=policy['raw_file_limit_bytes']
                total+=len(raw);assert total<=policy['raw_total_limit_bytes']
                target=B/row['local'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
                row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),git_blob_actual=blob,
                           status='SAVED' if blob==info['git_blob_sha1'] else 'HASH_MISMATCH_RETAINED')
            except Exception as e:row.update(status='FAILED_NO_RETRY',error=type(e).__name__)
            write(B/'access.json',visits)
    write(B/'fetch-complete.json',{'utc':utc(),'requests':len(visits),'bytes':total,
        'saved':sum(v['status']=='SAVED' for v in visits),'failed':sum(v['status']!='SAVED' for v in visits),
        'retry':0,'a_lock_sha256':seal['a_lock_sha256'],'new_candidate_count':len(inventory['new_candidates'])})
    print(json.dumps(read(B/'fetch-complete.json')))
if __name__=='__main__':{'select':select,'fetch':fetch}[sys.argv[1]]()
