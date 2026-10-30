"""Build new independent copies; no mutation of old source/evidence."""
import json,hashlib,ast
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parents[1]/'20261023/direct-api-v1';B=P.parent/'public-rag-next-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
    p=P/n;assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['transport.py']:
    assert not (P/name).exists();(P/name).write_bytes((OLD/name).read_bytes())
us=(OLD/'usage.py').read_text();tree=ast.parse(us);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='usage_record')
(P/'usage.py').write_text('"""Unchanged usage_record from audited prior source; no payload adaptation."""\nimport copy\n'+ast.get_source_segment(us,fn)+'\n',encoding='utf-8')
s=(OLD/'core.py').read_text();s=s.replace("BATCH=HERE.parent/'public-rag-all20-v1'","BATCH=HERE.parent/'public-rag-next-v1'")
s=s.replace("BATCH_SHA='72094112b5c0f6b72e920ad8d362c78ee5e302ee758b1e2de90c7c120b062d39'",'BATCH_SHA='+repr(sha(B/'packet-lock.json')))
s=s[:s.index('def verify_batch():')]+s[s.index('def extract(raw):'):]
s=s[:s.index('class Ledger:')]+s[s.index('def size(folder):'):]
s=s.replace("relative=f'originals/dataset_spec-to-rtl/{task}_{ext}'","relative=f'B/originals/dataset_spec-to-rtl/{task}_{ext}'")
s=s.replace("read(BATCH/'calibration-plan.json')['input_bindings'][relative]","read(BATCH/'B-lock.json')[relative.removeprefix('B/')]")
s=s.replace("read(BATCH/'calibration-plan.json')['tools'][str(Path(argv[0]))]","read(HERE/'tools-lock.json')[str(Path(argv[0]))]")
s=s.replace("if result['launch_error'] or result['limit_reason'] in ['resource_limit','cleanup_unknown']:","if result['launch_error'] or result['limit_reason']:")
s=s.replace("if len(matches)!=1 or matches[0][1]==0 or 'TIMEOUT' in text.upper():", "if 'TIMEOUT' in text.upper():return {'status':'RESOURCE_LIMIT','stage':'simulate','stop':True,'phases':phases,'reason':'original_tb_timeout'}\n if len(matches)!=1 or matches[0][1]==0:")
s=s.replace("if envelope.get('outcome')=='UNKNOWN':", "if envelope.get('outcome')=='RESPONSE_SIZE_LIMIT':return outcome('RESOURCE_LIMIT','transport',True)\n if envelope.get('outcome')=='UNKNOWN':")
s=s.replace("if body.get('model')!=slot.get('wire_model',slot['model']):", "if body.get('error') is not None:return outcome('SERVICE_ERROR','transport',True,upstream_error=body['error'])\n  if body.get('model')!=slot.get('wire_model',slot['model']):")
s=s.replace("if len(raw.encode())<=131072:save_bytes(Path(folder)/'model-output.txt',raw.encode())","if len(raw.encode())>131072:return outcome('RESOURCE_LIMIT','extraction',True,reason='text_bytes_exceed_131072')\n save_bytes(Path(folder)/'model-output.txt',raw.encode())")
(P/'core.py').write_text(s,encoding='utf-8')
put('tools-lock.json',{str(Path(p)):sha(Path(p)) for p in ['D:/iverilog/bin/iverilog.exe','D:/iverilog/bin/vvp.exe']})
(P/'route.json').write_bytes((B/'protocol/route.json').read_bytes())
put('reuse-provenance.json',{'core_source':str(OLD/'core.py'),'core_source_sha256':sha(OLD/'core.py'),'transport_byte_copy':sha(P/'transport.py')==sha(OLD/'transport.py'),'transport_source_sha256':sha(OLD/'transport.py'),'usage_record_unchanged':True,'input_packet_sha256':sha(B/'packet-lock.json'),'removed':'old verify_batch/Ledger and old20 calibration binding; no old runtime import','resource_changes':['text128KiB stop','tool timeout stop','TB TIMEOUT stop','HTTP200 embedded error stop']})
print('independent copies prepared')
