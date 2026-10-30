import collections,hashlib,json,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent
R=P.parents[2];SRC=P.parent/'main36-proxy-newbatch-v1';FIX=P.parent/'main36-school-homefix-v1'
def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
records=read(FIX/'records.json');rows=[];groups={};tasks={};cost=0
for rec in records:
 if rec['tool']!='vcs':continue
 job=SRC/'live/jobs'/('%03d'%rec['ordinal']);r=read(job/'result.json');local=r['local'];cost+=r['cost']
 row={k:rec[k] for k in ('ordinal','slot','task','model','condition','sample')}
 row.update(fixed_test=local['fixed_test'],synthesis=local['synthesis'],cost=r['cost'],rtl_sha256=sha((job/'dut.sv').read_bytes()))
 assert row['rtl_sha256']==r['rtl_sha256']
 rows.append(row)
 for table,key in ((groups,rec['model']),(tasks,rec['task'])):
  group=table.setdefault(key,{}).setdefault(rec['condition'],dict(total=0,pass_count=0,synthesis_pass=0))
  group['total']+=1;group['pass_count']+=local['fixed_test']=='FIXED_TEST_PASS';group['synthesis_pass']+=local['synthesis']=='SYNTH_PASS'
side=FIX/'shared-received/return-console-5fad7de7a61844f5.json';meta=read(side);archive=side.with_suffix('.zip');raw=archive.read_bytes()
assert sha(raw)==meta['archive_sha256']
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('console-manifest.json'));result=json.loads(z.read('console-result.json'))
 assert sha(z.read('console-manifest.json'))==meta['manifest_sha256']==records[0]['record']['manifest_sha256']
 for name,h in manifest['inputs'].items():assert sha(z.read(name))==h
 for name in ('dut.sv','testbench.sv','reference.sv'):assert z.read(name)==(SRC/'live/jobs/001'/name).read_bytes()
 assert result['status']=='CHECK_COUNT_DIFFERENT' and result['samples']==111
 evidence=P/'school-evidence-copy';evidence.mkdir(exist_ok=True)
 for name in ('testbench.sv','dut.sv','reference.sv','simulate.log','compile.log','console-result.json','console-manifest.json'):
  dest=evidence/name
  if dest.exists():assert dest.read_bytes()==z.read(name)
  else:dest.write_bytes(z.read(name))
paired=collections.Counter()
for row in rows:
 if row['condition']!='no_rag':continue
 other=next(r for r in rows if (r['task'],r['model'],r['sample'],r['condition'])==(row['task'],row['model'],row['sample'],'rag'))
 a=row['fixed_test']=='FIXED_TEST_PASS';b=other['fixed_test']=='FIXED_TEST_PASS'
 paired['both_pass' if a and b else 'both_fail' if not a and not b else 'rag_gain' if b else 'rag_loss']+=1
locks=read(P.parent/'main36-school-v1/source-results-lock.json')
for name,h in locks.items():assert sha((R/name).read_bytes())==h
summary=dict(rows=rows,by_model=groups,by_task=tasks,paired_by_sample_index=dict(paired),reported_new_cost_sum=round(cost,8),school_result=result,school_received=1,school_planned=144,source_lock_files_verified=len(locks),model_calls_this_analysis=0,eda_calls_this_analysis=0)
(P/'analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='rows'},ensure_ascii=False,indent=2))
