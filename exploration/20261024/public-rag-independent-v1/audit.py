"""Read-only evidence checks; never calls retrieve, HDL tools or network."""
import json,hashlib,re,datetime
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dig(b):return hashlib.sha256(b).hexdigest()
checks={};details={}
for stage in ['A','B','C','protocol']:
    lock=read(P/(stage+'-lock.json'))
    bad=[n for n,h in lock.items() if not (P/stage/n).is_file() or sha(P/stage/n)!=h]
    checks[stage+'_lock']=not bad and set(lock)=={f.relative_to(P/stage).as_posix() for f in (P/stage).rglob('*') if f.is_file()}
    details[stage]={'files':len(lock),'mismatches':bad,'lock_sha256':sha(P/(stage+'-lock.json'))}
checks['plan_lock']=all(sha(P/n)==h for n,h in read(P/'plan-lock.json').items())
a=read(P/'A-seal.json');b=read(P/'B-seal.json');c=read(P/'C-seal.json')
checks['seal_bindings']=(a['a_lock_sha256']==sha(P/'A-lock.json') and a['protocol_lock_sha256']==sha(P/'protocol-lock.json') and b['b_lock_sha256']==sha(P/'B-lock.json') and c['c_lock_sha256']==sha(P/'C-lock.json'))
checks['chronology']=a['frozen_utc']<read(P/'B/start.json')['utc']<read(P/'B/fetch-complete.json')['utc']<b['frozen_utc']<read(P/'C/start.json')['utc']<c['frozen_utc']
chunks=read(P/'A/chunks.json');raw=(P/'A/sources/VerilogCodingStyle.md').read_bytes();src=read(P/'A/source-manifest.json')['source']
checks['full_source_reconstruction']=''.join(x['text'] for x in chunks).encode()==raw and len(chunks)==48 and all(0<len(x['text'])<=2048 and dig(x['text'].encode())==x['sha256'] for x in chunks)
checks['source_license_hash']=dig(raw)==src['original_sha256'] and sha(P/'A/sources/LICENSE')==src['license_sha256']
cfg=read(P/'protocol/overlay.json');hist=read(P/'A/history-exclusions.json');tree=read(P/'A/metadata/tree.json')['tree']
metadata=sorted(Path(x['path']).name[:-11] for x in tree if x['path'].startswith('dataset_spec-to-rtl/') and x['path'].endswith('_prompt.txt'))
excluded={x['id']:x['reason'] for x in cfg['metadata_exclusions']}
expected={i:('PRIOR_READ_OR_USED' if i in hist['exposed_ids'] else 'CONSERVATIVE_HISTORY_FAMILY') for i in metadata if i in hist['exposed_ids'] or re.search(hist['metadata_family_regex'],i,re.I)}
checks['exclusion_denominator']=len(metadata)==156 and len(excluded)==83 and excluded==expected
remaining=sorted(set(metadata)-set(excluded),key=lambda i:dig((cfg['seed']+'\n'+i).encode()))
checks['fixed_first20']=len(remaining)==73 and remaining[:20]==[x['id'] for x in cfg['new_candidates']]
access=read(P/'B/access.json');bad=[]
for r in access:
    path=P/r['local'];data=path.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    expected_blob=next(t['sha'] for t in tree if 'B/originals/'+t['path']==r['local'])
    if not(r['status']=='SAVED' and dig(data)==r['sha256'] and blob==r['expected_git_blob']==r['actual_git_blob']==expected_blob):bad.append(r['local'])
checks['all60_originals']=len(access)==60 and len({r['local'] for r in access})==60 and not bad
checks['no_source_retry']=read(P/'B/fetch-complete.json')['requests']==60 and read(P/'B/fetch-complete.json')['retry']==0
selection=read(P/'B/selection.json');ids=selection['selected_ids'];rows=selection['rows']
checks['selection_before_retrieval']=ids==[r['id'] for r in rows if r['eligible']][:8] and len(rows)==20 and len(ids)==2 and b['retrieval_calls_so_far']==0
slots=read(P/'C/slots.json');stats=read(P/'C/retrieval-manifest.json');system=(P/'A/system.txt').read_bytes().decode();template=(P/'A/context-template.txt').read_bytes().decode()
message_checks=[];byte_checks=[];retrieval_checks=[]
for task in ids:
    query=(P/'B/originals/dataset_spec-to-rtl'/f'{task}_prompt.txt').read_bytes().decode();rr=read(P/'C/retrieval'/f'{task}.json')
    rankings=rr['rankings'];expected_ids=[v['chunk_id'] for v in sorted(rankings,key=lambda v:(-v['score'],v['chunk_id'])) if v['score']>0][:3]
    chosen=[next(x for x in chunks if x['id']==i) for i in expected_ids]
    fragments='\n\n'.join(f"[{x['id']}; lowRISC Verilog Coding Style Guide; lines {x['start_line']}-{x['end_line']}]\n{x['text']}" for x in chosen)
    context=template.format(fragments=fragments) if chosen else ''
    retrieval_checks.append(rr['query']==query and rr['query_sha256']==dig(query.encode()) and len(rankings)==48 and rr['selected_ids']==expected_ids and rr['selected_chunks']==chosen and rr['context_sha256']==dig(context.encode()) and (P/'C/contexts'/f'{task}.txt').read_bytes()==context.encode() and all(abs(sum(t['contribution'] for t in v['matched'])-v['score'])<1e-12 for v in rankings))
    for cond in cfg['conditions']:
        group=[s for s in slots if s['task']==task and s['condition']==cond];normalized=[]
        messages=[{'role':'system','content':system},{'role':'user','content':query+(context if cond=='rag' else '')}]
        for s in group:
            req=read(P/s['request']);data=(P/s['request']).read_bytes()
            message_checks.append(req['messages']==messages and sha(P/s['request'])==s['request_sha256'] and s['messages_sha256']==dig(json.dumps(messages,ensure_ascii=False,separators=(',',':')).encode()) and req['model']=='openai/'+s['model'] and set(req)=={'model','messages','stream','provider'} and req['provider']=={'only':['openai'],'allow_fallbacks':False,'require_parameters':True} and req['stream'] is False)
            normalized.append(data.replace(json.dumps(req['model']).encode(),b'"FIXED_MODEL"',1))
        byte_checks.append(len(group)==6 and len(set(normalized))==1)
checks['stored_retrieval_integrity_no_rerun']=len(stats)==2 and all(retrieval_checks)
checks['complete_messages_exact']=all(message_checks)
checks['request_bytes_only_model_diff']=all(byte_checks)
checks['24_not_started']=len(slots)==24 and all(s['status']=='NOT_STARTED' and s['reserved'] is False for s in slots) and len({s['id'] for s in slots})==24
expected_order=[(t,cond,model,sample) for t in ids for cond in cfg['conditions'] for model in cfg['models'] for sample in [1,2]]
checks['slot_order']=expected_order==[(s['task'],s['condition'],s['model'],s['sample']) for s in slots]
checks['no_execution_artifacts']=not(P/'runtime').exists() and not(P/'technical-release.json').exists() and read(P/'C/summary.json')['model_calls']==read(P/'C/summary.json')['eda_calls']==0
checks['generic_fixtures']=read(P/'generic-check.json')['passed']
# Historical sealed file hashing only; no parsing outcomes or modifying files.
pres=[]
for root in [P.parent/'public-rag-next-v1',P.parent/'public-rag-next-executor-v1',P.parent.parent/'20261023/public-rag-all20-v1',P.parent.parent/'20261023/cli-cache-repair-v1']:
    lock=read(root/'packet-lock.json');bad=[n for n,h in lock.items() if not(root/n).is_file() or sha(root/n)!=h]
    pres.append({'root':str(root),'files_checked':len(lock),'lock_sha256':sha(root/'packet-lock.json'),'mismatches':bad})
checks['historical_packets_unchanged']=all(not x['mismatches'] for x in pres)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':all(checks.values()),'checks':checks,'stage_details':details,'preservation':pres,'limits':['Structural/source/request audit, not HDL correctness or independent reviewer verdict','Stored retrieval scores/slices checked without rerunning real query retrieval','No model/HDL/network calls; historical files hashed only','No claim of cognitive blindness or training-unseen tasks']}
dest=P/'audit.json';assert not dest.exists();dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':out['passed'],'checks':len(checks),'failures':[k for k,v in checks.items() if not v],'preserved_files':sum(x['files_checked'] for x in pres)}))
