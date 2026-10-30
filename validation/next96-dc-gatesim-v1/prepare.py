import sys,json,shutil,zipfile,io,ast,tempfile
from pathlib import Path
OUT=Path(__file__).resolve().parent;LAB=OUT.parents[1]
sys.path.insert(0,str(OUT))
import school_sim as s
src=LAB/'exploration/20261024/public-rag-next-executor-v1/runtime/live-run/jobs/025'
dc=LAB/'validation/next96-school-single-v1/returned-20261024T061542Z'
review=s.read(LAB/'validation/next96-school-single-v1/return-audit.json')
assert s.sha(dc/'outputs/netlist.v')==review['evidence_hashes']['outputs/netlist.v']
payload=OUT/'payload';payload.mkdir(exist_ok=False)
for name in ('testbench.sv','reference.sv'):(payload/name).write_bytes((src/name).read_bytes())
(payload/'netlist.v').write_bytes((dc/'outputs/netlist.v').read_bytes())
shutil.copyfile(OUT/'school_sim.py',payload/'school_sim.py')
s.save(payload/'manifest.json',dict(key=s.KEY,slot=25,job='Prob094_gatesv__no_rag__gpt-5.6-luna__s001',netlist_sha256=s.sha(dc/'outputs/netlist.v'),source_rtl_sha256=s.sha(src/'dut.sv'),source_testbench_sha256=s.sha(src/'testbench.sv'),source_reference_sha256=s.sha(src/'reference.sv'),expected_samples=213,scope='Original fixed TB, zero-delay functional model; no SDF/formal equivalence; cross-simulator random streams not guaranteed identical',school_model_sha256=s.MODEL_HASH))
s.save(payload/'payload-lock.json',{n:s.sha(payload/n) for n in sorted(s.INPUTS)})
s.verify(payload)
# Offline acceptance tests: no commercial tool execution.
checks={}
checks['python36_syntax']=bool(ast.parse((payload/'school_sim.py').read_text(),feature_version=(3,6)))
checks['pass_parser']=s.verdict('Mismatches: 0 in 213 samples\n',0)['status']=='FIXED_TEST_PASS'
checks['fail_parser']=s.verdict('Mismatches: 1 in 213 samples\n',0)['status']=='FUNCTION_FAIL'
checks['wrong_denominator']=s.verdict('Mismatches: 0 in 212 samples\n',0)['status']=='CHECK_COUNT_DIFFERENT'
checks['duplicate_summary_rejected']=s.verdict('Mismatches: 0 in 213 samples\n'*2,0)['status']=='INVALID_OR_TIMEOUT_RECEIPT'
checks['tool_error_not_pass']=s.verdict('Mismatches: 0 in 213 samples\n',1)['status']=='TOOL_ERROR'
checks['timeout_not_pass']=s.verdict('TIMEOUT\nMismatches: 0 in 213 samples\n',0)['status']=='INVALID_OR_TIMEOUT_RECEIPT'
with tempfile.TemporaryDirectory(prefix='next96-package-test-') as temp:
    root=Path(temp);s.reserve(root/'one')
    try:s.reserve(root/'one');checks['repeat_blocked']=False
    except FileExistsError:checks['repeat_blocked']=True
    shutil.copytree(payload,root/'bad')
    with (root/'bad/reference.sv').open('ab') as f:f.write(b'\n')
    try:s.verify(root/'bad');checks['tamper_blocked']=False
    except ValueError:checks['tamper_blocked']=True
assert all(checks.values()),checks
archive=OUT/(s.KEY+'.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for n in sorted(s.INPUTS|{'payload-lock.json'}):z.write(payload/n,n)
digest=s.sha(archive)
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())==s.INPUTS|{'payload-lock.json'} and z.testzip() is None
    assert all(z.read(n)==(payload/n).read_bytes() for n in z.namelist())
checks['archive_roundtrip']=True
bootstrap='''#!/usr/bin/env bash
set -eu
share_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$share_dir/ARCHIVE" "DIGEST" "$share_dir" <<'PY_BOOT'
import hashlib,io,os,sys,tempfile,zipfile
from pathlib import Path
blob=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest()!=sys.argv[2]:raise SystemExit('STOP: ZIP hash mismatch')
allowed={'school_sim.py','manifest.json','testbench.sv','reference.sv','netlist.v','payload-lock.json'}
work=Path(tempfile.mkdtemp(prefix='next96-gate-payload-',dir=str(Path.home())))
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    if set(z.namelist())!=allowed or len(z.namelist())!=len(allowed) or z.testzip() is not None:raise SystemExit('STOP: Unexpected ZIP')
    for name in sorted(allowed):(work/name).write_bytes(z.read(name))
os.execv(sys.executable,[sys.executable,str(work/'school_sim.py'),'run','--return-dir',sys.argv[3]])
PY_BOOT
'''.replace('ARCHIVE',archive.name).replace('DIGEST',digest)
starter=OUT/'start_dc25_xcelium.sh';starter.write_text(bootstrap,encoding='utf-8',newline='\n')
shared=Path('C:/Users/A/Documents/FYP/ECE-Next96')
for p in (archive,starter):
    target=shared/p.name
    if target.exists():assert s.sha(target)==s.sha(p)
    else:shutil.copyfile(p,target)
s.save(OUT/'offline-verification.json',dict(checks=checks,model_calls=0,commercial_tool_calls=0,archive_sha256=digest,shared=str(shared),status='OFFLINE_PACKAGE_VERIFIED_SCHOOL_RUN_PENDING'))
print(json.dumps(s.read(OUT/'offline-verification.json'),indent=2))
