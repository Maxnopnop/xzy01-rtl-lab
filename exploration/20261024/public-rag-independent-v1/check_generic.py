"""Generic word fixtures only; no benchmark inputs or tuning."""
import json,importlib.util,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('generic',P/'A/retriever.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
toy=[{'id':'a','text':'apple apple pear'},{'id':'b','text':'orange'},{'id':'c','text':'apple apple pear'}]
r=m.retrieve('apple apple pear',toy);z=m.retrieve('unseenword',toy)
source=(P/'A/sources/VerilogCodingStyle.md').read_bytes();chunks=json.loads((P/'A/chunks.json').read_bytes())
checks={'self_cosine':abs(r['rankings'][0]['score']-1)<1e-12,'tie_by_id':r['selected_ids']==['a','c'],'oov_no_fallback':z['selected_ids']==[] and z['no_hit'],'no_stopwords':m.terms('The A apple')==['the','a','apple'],'source_reconstruction':''.join(c['text'] for c in chunks).encode()==source,'all_chunk_hashes':all(hashlib.sha256(c['text'].encode()).hexdigest()==c['sha256'] for c in chunks),'cap':len(chunks)==48 and all(len(c['text'])<=2048 for c in chunks)}
assert all(checks.values())
(P/'generic-check.json').write_text(json.dumps({'checks':checks,'passed':True,'queries':'synthetic fruit words only; not used to select/change parameters','benchmark_retrievals':0,'model_calls':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks))
