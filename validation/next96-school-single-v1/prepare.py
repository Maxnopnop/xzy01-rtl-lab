"""Package one retained next96 RTL for manual school DC; no EDA/model call."""
import sys,json,uuid,zipfile,shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
sys.path.insert(0,str(LAB))
import ece_synth_common as c
RUN=LAB/'exploration/20261024/public-rag-next-executor-v1/runtime/live-run'
slots=c.read(LAB/'exploration/20261024/public-rag-next-v1/C/slots.json')
s=next(s for s in slots if s['ordinal']==25)
rpath=RUN/'results'/(s['id']+'.json');result=c.read(rpath)
assert result['status']=='REFERENCE_PASS'
local=c.read(LAB/'validation/next96-synthesis-v1/jobs/025/result.json')
assert local['synthesis_status']=='SYNTH_PASS'
source=RUN/'jobs/025/dut.sv';assert c.sha(source)==local['rtl_sha256']
key='next96-dc-slot025-v2';dest=OUT/key;dest.mkdir(exist_ok=False)
shared=Path('C:/Users/A/Documents/FYP/ECE-Next96');shared.mkdir(exist_ok=True)
profile=dict(c.read(LAB/'config.local.synthesis.json')['tools']['dc'])
profile.update(sdc_file='constraints.sdc',constraints_reviewed=True)
(dest/'dut.sv').write_bytes(source.read_bytes())
(dest/'constraints.sdc').write_text('''# Combinational smoke constraint, no clock/reset ports.
# 10 library time units input-to-output, provisional engineering target.
# No external input delay, transition, output load or PPA claim.
set_max_delay 10.0 -from [all_inputs] -to [all_outputs]
''',encoding='utf-8')
nonce=uuid.uuid4().hex
meta=dict(schema=1,package_id=key,tool='dc',top='TopModule',job_id=s['id'],source_result_sha256=c.sha(rpath),source_plan_sha256=c.sha(LAB/'exploration/20261024/public-rag-next-v1/C/slots.json'),rtl_sha256=c.sha(source),sdc_sha256=c.sha(dest/'constraints.sdc'),original_simulation=result['status'],nonce=nonce,profile=profile,expected_tool=c.TOOLS['dc'],note='Single flow validation, not representative model comparison. 10 library time-unit combinational max delay is provisional, not original task requirement. Review library units and timing before interpretation.')
c.save(dest/'job.json',meta)
tcl=c.tcl('dc','TopModule',profile,nonce)
tcl=tcl.replace('source constraints.sdc','foreach_in_collection lib [get_libs *] { report_lib [get_object_name $lib] }\nsource constraints.sdc')
(dest/'synthesis.tcl').write_text(tcl,encoding='utf-8',newline='\n')
(dest/'launch.csh').write_text(c.launcher('dc'),encoding='utf-8',newline='\n')
for name in ('ece_synth_common.py','ece_synth_school.py'):shutil.copyfile(LAB/name,dest/name)
c.save(dest/'payload-lock.json',{name:c.sha(dest/name) for name in sorted(c.INPUTS)})
assert c.verify(dest)==meta
archive=OUT/(key+'.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for name in sorted(c.INPUTS|{'payload-lock.json'}):z.write(dest/name,name)
c.copy_once(archive,shared/archive.name)
for name in ('ece_synth_common.py','ece_synth_school.py','ece_synth_menu.sh'):c.copy_once(LAB/name,shared/name)
row=dict(package_id=key,archive=archive.name,archive_sha256=c.sha(archive),tool='dc',job_id=s['id'],readiness='READY_FOR_SCHOOL_PREFLIGHT')
c.save(shared/'synthesis-catalog.json',dict(schema=1,packages=[row]))
c.save(OUT/'binding.json',dict(**row,source_result=str(rpath),source_rtl=str(source),shared_dir=str(shared),model_calls=0,eda_calls=0))
# Verify actual ZIP extraction without executing any school tool.
c.extract(archive,OUT/'unpack-check-v2',c.INPUTS|{'payload-lock.json'})
assert c.verify(OUT/'unpack-check-v2')==meta
print(json.dumps(dict(package=str(shared/archive.name),rtl_sha256=meta['rtl_sha256'],source_slot=25,archive_sha256=c.sha(archive),offline_package_verified=True),indent=2))
