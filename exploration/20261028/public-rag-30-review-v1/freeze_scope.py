"""Metadata-only scope freeze, before reading the ten additional candidate bodies."""
import datetime,hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
OLD=R/'exploration/20261024/public-rag-independent-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (P/'scope.json').exists()
source=R/'validation/console-v3-recovery-r1-20261028/delivery-source-lock.json'
v3=read(source);assert all(sha(R/n)==h for n,h in v3.items())
assert v3['console_bridge_v3.py']=='492bb008b8d42c524a9241ea437ecb9b89f004cc9a1a08028687f69ec12816f5'
packet=read(OLD/'packet-lock.json');assert all(sha(OLD/n)==h for n,h in packet.items())
alock=read(OLD/'A-lock.json');assert all(sha(OLD/'A'/n)==h for n,h in alock.items())
aseal=read(OLD/'A-seal.json');bs=read(OLD/'B/start.json')
assert sha(OLD/'A-lock.json')==aseal['a_lock_sha256'] and aseal['frozen_utc']<bs['utc']
overlay=read(OLD/'protocol/overlay.json');adopt=read(R/'exploration/20261024/public-rag-all20-reconsider-v1/adoption.json')
assert adopt['task_order']==overlay['remaining_ordered_ids'][:20]
tree=read(OLD/'A/metadata/tree.json');blobs={x['path']:x['sha'] for x in tree['tree'] if x['type']=='blob'}
ids=adopt['task_order']+overlay['remaining_ordered_ids'][20:30];assert len(set(ids))==30
scope={'frozen_utc':utc(),'status':'CANDIDATE_SCOPE_ONLY','existing_exact30_found':False,'search_scope':'exploration/validation filenames for 30/candidate; existing adopted20 and frozen overlay contain definitive ordered metadata','commit':overlay['dataset_commit'],'seed':overlay['seed'],'selection_rule':'Adopted20 plus positions21..30 of existing remaining_ordered_ids; no replacement, no retrieval/content/result filtering','max_additional_candidates':10,'max_public_GET':30,'automatic_retries':0,'max_reference_compile':30,'max_reference_simulate':30,'models':['openai/gpt-4o-mini','openai/gpt-4.1-mini','openai/gpt-5.6-luna'],'samples':2,'conditions':['no_rag','rag'],'calls_only':True,'opportunity_ceiling':360,'tasks':[{'rank':i+1,'id':t,'prior_adopted':i<20,'files':{ext:{'path':f'dataset_spec-to-rtl/{t}_{ext}','git_blob_sha1':blobs[f'dataset_spec-to-rtl/{t}_{ext}']} for ext in ('prompt.txt','ref.sv','test.sv')}} for i,t in enumerate(ids)],'additional_body_reads_before_freeze':0,'cognitive_blind':False,'training_contamination':'UNKNOWN'}
put(P/'scope.json',scope)
put(P/'scope-seal.json',{'utc':utc(),'scope_sha256':sha(P/'scope.json'),'old_A_seal':aseal,'old_B_start':bs,'v3_source_lock_sha256':sha(source)})
shutil.copytree(OLD/'A',P/'A')
for f in ['A-lock.json','A-seal.json','B/start.json','protocol/overlay.json']:
 dst=P/'prior'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/f,dst)
shutil.copyfile(source,P/'v3-source-lock.json')
put(P/'preservation-before.json',dict({str((OLD/n).relative_to(R)).replace('\\','/'):h for n,h in packet.items()},**v3))
print(json.dumps({'scope_sha256':sha(P/'scope.json'),'new_ids':ids[20:],'A_files_verified':len(alock),'old_packet_files_verified':len(packet),'v3_files_verified':len(v3)}))
