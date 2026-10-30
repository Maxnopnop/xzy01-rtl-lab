"""Independent read-only validation and TF-IDF recomputation; no execution imports."""
import hashlib,json,math,re
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'exploration/20261024/public-rag-independent-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    checked={}
    for stage in ('A','B','C','protocol'):
        lock=read(ROOT/(stage+'-lock.json'))
        for name,h in lock.items():assert sha((ROOT/stage/name).read_bytes())==h,(stage,name)
        checked[stage]=len(lock)
    a,b,c=[read(ROOT/(s+'-seal.json')) for s in 'ABC']
    assert a['frozen_utc']<read(ROOT/'B/start.json')['utc']<b['frozen_utc']<read(ROOT/'C/start.json')['utc']<c['frozen_utc']
    overlay=read(ROOT/'protocol/overlay.json');selection=read(ROOT/'B/selection.json')
    assert len(selection['rows'])==20
    assert [r['id'] for r in selection['rows']]==[r['id'] for r in overlay['new_candidates']]
    blob_count=0
    for item in overlay['new_candidates']:
        for f in item['files'].values():
            raw=(ROOT/'B/originals'/f['path']).read_bytes()
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==f['git_blob_sha1']
            blob_count+=1
    old=set()
    for batch, slot_path in (('20261023/public-rag-all20-v1','slots.json'),('20261024/public-rag-next-v1','C/slots.json')):
        old.update(s['task'] for s in read(HERE.parents[1]/'exploration'/batch/slot_path))
    assert not old.intersection(selection['selected_ids'])
    chunks=read(ROOT/'A/chunks.json');text=(ROOT/'A/sources/VerilogCodingStyle.md').read_bytes().decode()
    assert ''.join(x['text'] for x in chunks)==text
    tokens=lambda s:re.findall(r'[a-z_][a-z0-9_]*',s.lower())
    docs=[Counter(tokens(x['text'])) for x in chunks];vocab=set().union(*(set(x) for x in docs))
    weights={w:1+math.log((1+len(docs))/(1+sum(w in d for d in docs))) for w in vocab}
    def vector(bag):
        v={w:(1+math.log(n))*weights[w] for w,n in bag.items() if w in weights}
        norm=math.sqrt(math.fsum(x*x for x in v.values()))
        return {w:x/norm for w,x in v.items()} if norm else {}
    dv=[vector(d) for d in docs];retrievals={}
    for task in selection['selected_ids']:
        raw=(ROOT/'B/originals/dataset_spec-to-rtl'/(task+'_prompt.txt')).read_bytes()
        r=read(ROOT/'C/retrieval'/(task+'.json'));assert raw.decode()==r['query']
        qv=vector(Counter(tokens(raw.decode())))
        scores={ch['id']:math.fsum(qv[w]*v.get(w,0) for w in qv) for ch,v in zip(chunks,dv)}
        ids=sorted(scores,key=lambda k:(-scores[k],k));expected=[k for k in ids if scores[k]>0][:3]
        assert expected==r['selected_ids']
        for row in r['rankings']:assert abs(row['score']-scores[row['chunk_id']])<1e-12
        retrievals[task]=expected
    groups=defaultdict(list);slots=read(ROOT/'C/slots.json')
    assert len(slots)==24
    for s in slots:
        raw=(ROOT/s['request']).read_bytes();assert sha(raw)==s['request_sha256']
        obj=json.loads(raw);assert obj.pop('model')==s['wire_model']
        groups[(s['task'],s['condition'])].append(obj)
        assert s['status']=='NOT_STARTED' and not s['reserved']
        if s['condition']=='no_rag':
            prompt=(ROOT/'B/originals/dataset_spec-to-rtl'/(s['task']+'_prompt.txt')).read_bytes().decode()
            assert obj['messages'][-1]['content']==prompt
    for rows in groups.values():assert len(rows)==6 and all(r==rows[0] for r in rows)
    report=dict(passed=True,lock_files=checked,verified_git_blobs=blob_count,candidates=20,
                conditional_selected=selection['selected_ids'],excluded=18,recomputed_retrievals=retrievals,
                request_count=24,equal_request_groups=len(groups),new_model_calls=0,new_eda_calls=0,
                limits=['Same-source reference; no independent oracle or actual reference simulation in this package',
                        'Historical full-function near-duplicate judgment remains semantic review, not mathematical disjointness',
                        'No cognitive-blindness or model-training-unseen claim'])
    (HERE/'rag-coordinator-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
