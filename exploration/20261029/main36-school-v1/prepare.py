"""Prepare 144 individually invoked school packages; never starts tools."""
import copy,hashlib,json,shutil,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];SRC=P.parent/'main36-proxy-newbatch-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,o):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)
def raw(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(v)
lock=read(R/'validation/console-v3-recovery-r1-20261028/delivery-source-lock.json')
names=('console_bridge_v3.py','console_catalog_v3.py','console_school_v3.py','console_school_runner_v3.py','console_stage_v3.py','console_dependencies.json','rtl_lab.py','ece_synth_common.py','ece_synth_school.py')
deps=read(R/'console_dependencies.json')
for n in names:
 assert sha(R/n)==(lock.get(n) or deps[n]),n
 raw(P/'reuse'/n,(R/n).read_bytes())
sys.path.insert(0,str(P/'reuse'));import console_bridge_v3 as b;import console_school_v3 as school
b.STATE=P/'state'
batch=read(SRC/'batch.json');parent=read(SRC/'inputs/parent-manifest.json')
assert len(batch['slots'])==36
for n,h in batch['files'].items():
 assert sha(SRC/'inputs'/n)==h
 raw(P/'inputs'/n,(SRC/'inputs'/n).read_bytes())
manifest=copy.deepcopy(parent);manifest.update(name='main36-school-export-only',purpose='SCHOOL_EXPORT_ONLY',slots=batch['slots'],max_calls=36,model_execution_authorized=False)
put(P/'inputs/console-package.json',manifest)
pkg=b.Package(P/'inputs/console-package.json')
src_lock={};rows=[]
for s in batch['slots']:
 folder=SRC/'live/jobs'/f"{s['ordinal']:03d}"
 row=dict(s,dataset='main36-proxy',job_dir=str(folder),result_path=str(folder/'result.json'),manifest_path=str(pkg.path),manifest_sha256=pkg.identity)
 prov=b.validate_saved_inputs(row)
 for n,h in prov.items():src_lock[(folder/n).relative_to(R).as_posix()]=h
 for f in (folder/'local').rglob('*'):
  if f.is_file():src_lock[f.relative_to(R).as_posix()]=sha(f)
 assert read(folder/'result.json')['status']=='GENERATED_UNVERIFIED'
 rows.append(row)
put(P/'source-results-lock.json',src_lock)
raw(P/'constraints/comb.sdc',b'# Engineering smoke only, not a specification/PPA signoff target.\n# 10 library time units; no external drive or load model.\nset_max_delay 10.0 -from [all_inputs] -to [all_outputs]\n')
raw(P/'constraints/rule110.sdc',b'# Engineering smoke only: original specification gives no frequency.\n# Clock period 10 library time units, zero external IO delay, no load model.\ncreate_clock -name smoke_clk -period 10.0 [get_ports clk]\nset_input_delay 0.0 -clock smoke_clk [get_ports {load data*}]\nset_output_delay 0.0 -clock smoke_clk [get_ports {q*}]\n')
profiles=read(R/'validation/console-school-four-slot025-v1/school-profile.json')['tools']
put(P/'constraints-review.json',{'status':'STATIC_ENGINEERING_SMOKE_REVIEW','reviewer':'exploration','basis':'Original 055/072 purely combinational; 124 specifies positive-edge clk/load/data/q. 10 units is provisional shared engineering constraint, not task requirement.','comb_tasks':['Prob055_conditional','Prob072_thermostat'],'clock_task':'Prob124_rule110','port_patterns':['clk','load','data*','q*'],'ppa_signoff':False,'external_delays':'zero for clocked smoke only','library_profiles_source':'validation/console-school-four-slot025-v1/school-profile.json','sdc_sha256':{p.name:sha(p) for p in (P/'constraints').iterdir()}})
put(P/'profiles.json',profiles)
out=P/'outgoing';out.mkdir()
records=[]
for row in rows:
 for tool in ('vcs','xcelium','dc','genus'):
  sdc=P/'constraints'/('rule110.sdc' if row['task']=='Prob124_rule110' else 'comb.sdc')
  rec=school.pack(row,tool,out,profiles.get(tool),sdc if tool in profiles else None)
  item={'ordinal':row['ordinal'],'slot':row['id'],'task':row['task'],'model':row['model'],'condition':row['condition'],'sample':row['sample'],'tool':tool,'expected_checks':row['expected_checks'],'record':rec}
  put(P/'records'/f"{row['ordinal']:03d}-{tool}.json",item);records.append(item)
 print(json.dumps({'prepared_ordinal':row['ordinal'],'tools':4}),flush=True)
put(P/'records.json',records)
put(P/'preparation-audit.json',{'cases':36,'tool_cases':len(records),'original_files_unchanged':all(sha(R/n)==h for n,h in src_lock.items()),'model_calls':0,'school_calls':0,'shared_not_yet_published':True})
