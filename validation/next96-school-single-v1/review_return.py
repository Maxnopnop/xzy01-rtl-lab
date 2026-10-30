import sys,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
sys.path.insert(0,str(LAB))
import ece_synth_common as c
import ece_synthesis as synthesis
shared=Path('C:/Users/A/Documents/FYP')
side=shared/'return-synth-20261024T061542Z-8bbc5980.json'
meta=c.read(side)
assert meta['package_id']=='next96-dc-slot025-v2'
assert Path(meta['archive']).name==meta['archive']
archive=shared/meta['archive'];assert c.sha(archive)==meta['archive_sha256']
original=OUT/'next96-dc-slot025-v2'
assert meta['input_lock_sha256']==c.sha(original/'payload-lock.json')
target=OUT/'returned-20261024T061542Z'
if not target.exists():c.extract(archive,target,c.INPUTS|c.ARTIFACTS|{'payload-lock.json'})
job=c.verify(target);assert job==c.verify(original)
status=synthesis.judge(target,original)
binding=c.read(OUT/'binding.json')
assert c.sha(Path(binding['source_rtl']))==job['rtl_sha256']
assert c.sha(Path(binding['source_result']))==job['source_result_sha256']
summary=dict(status=status,package=job['package_id'],job=job['job_id'],execution=c.read(target/'execution.json'),doctor=c.read(target/'doctor.json'),rtl_source_unchanged=True,archive_sha256=meta['archive_sha256'],evidence_hashes={p.relative_to(target).as_posix():c.sha(p) for p in target.rglob('*') if p.is_file()},model_calls=0,eda_calls=0)
c.save(OUT/'return-audit.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k!='evidence_hashes'},ensure_ascii=False,indent=2))
