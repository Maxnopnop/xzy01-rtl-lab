"""Generic TF-IDF cosine: no model, benchmark list, learned parameters or network."""
import re,math,hashlib
from collections import Counter
def digest(raw):return hashlib.sha256(raw).hexdigest()
def terms(s):return re.findall(r'[a-z_][a-z0-9_]*',s.lower())
def chunk_document(text):
    chunks=[];offset=0;buffer=''
    # Greedy whole-line packing. Oversize single lines split mechanically.
    def add(body):
        nonlocal offset
        if not body:return
        chunks.append({'id':f'GEN{len(chunks)+1:03d}','text':body,'char_start':offset,'char_end':offset+len(body),'start_line':text.count('\n',0,offset)+1,'end_line':text.count('\n',0,offset+len(body)-1)+1,'sha256':digest(body.encode()),'source_id':'lowrisc-full'})
        offset+=len(body)
    for line in text.splitlines(keepends=True):
        if len(buffer)+len(line)>2048:add(buffer);buffer=''
        while len(line)>2048:add(line[:2048]);line=line[2048:]
        buffer+=line
    add(buffer)
    assert ''.join(c['text'] for c in chunks)==text
    assert 0<len(chunks)<=60 and all(len(c['text'])<=2048 for c in chunks)
    return chunks
def retrieve(query,chunks):
    bags=[Counter(terms(c['text'])) for c in chunks];N=len(bags)
    vocab=sorted(set().union(*(set(b) for b in bags)))
    df={t:sum(t in b for b in bags) for t in vocab}
    idf={t:math.log((1+N)/(1+df[t]))+1 for t in vocab}
    def vec(b):
        w={t:(1+math.log(b[t]))*idf[t] for t in sorted(b) if t in idf}
        norm=math.sqrt(sum(v*v for v in w.values()))
        return {t:v/norm for t,v in w.items()} if norm else {}
    q=vec(Counter(terms(query)));rows=[]
    for c,b in zip(chunks,bags):
        d=vec(b);matched=[{'term':t,'contribution':q[t]*d[t]} for t in sorted(q.keys()&d.keys())]
        rows.append({'chunk_id':c['id'],'score':sum(x['contribution'] for x in matched),'matched':matched})
    ranked=sorted(rows,key=lambda r:(-r['score'],r['chunk_id']));selected=[r['chunk_id'] for r in ranked if r['score']>0][:3]
    return {'query':query,'query_sha256':digest(query.encode()),'rankings':ranked,'selected_ids':selected,'no_hit':not selected,'oov_terms':sorted(set(terms(query))-set(vocab))}
