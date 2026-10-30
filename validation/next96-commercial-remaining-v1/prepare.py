"""Prepare three independent manual cases; never execute school tools."""
import ast,hashlib,importlib.util,json,shutil,tempfile,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent;LAB=OUT.parents[1]
BASE=LAB/'validation/next96-dc-gatesim-v1'
SRC=LAB/'exploration/20261024/public-rag-next-executor-v1/runtime/live-run/jobs/025'
DC=LAB/'validation/next96-school-single-v1/returned-20261024T061542Z/outputs/netlist.v'
SHARED=Path('C:/Users/A/Documents/FYP/ECE-Next96')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def change(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)
source=(BASE/'school_sim.py').read_text()
spec=importlib.util.spec_from_file_location('basegate',BASE/'school_sim.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
dc_old='next96-dc-slot025-xcelium-v1'
cases=[('xcelium-rtl','next96-rtl-slot025-xcelium-v1',False,False),('vcs-rtl','next96-rtl-slot025-vcs-v1',False,True),('vcs-dc','next96-dc-slot025-vcs-v1',True,True)]
catalog=[]
for selector,key,gate,vcs in cases:
    folder=OUT/key;folder.mkdir(exist_ok=False)
    code=change(source,"KEY='"+dc_old+"'","KEY='"+key+"'")
    if not gate:
        code=code.replace("'netlist.v'","'dut.sv'").replace('reference.sv netlist.v','reference.sv dut.sv')
        code=change(code,"    if sha(MODEL)!=MODEL_HASH:raise ValueError('Model hash differs; no simulation started')\n",'')
        code=change(code,"    if sha(Path.home()/'xzy01-next96-q38Nji/package/outputs/netlist.v')!=m['netlist_sha256']:raise ValueError('School DC netlist changed')\n",'')
        code=change(code,"model_path=MODEL,model_sha256=sha(MODEL)","model_path=None,model_sha256=None")
        code=change(code,"functional_defines=['TETRAMAX']","functional_defines=[]")
        code=change(code,"        if sha(MODEL)!=MODEL_HASH:raise ValueError('Library changed during simulation')\n",'')
        code=code.replace(' +define+TETRAMAX -nospecify','').replace(' -v "MODEL_PATH" +incdir+"MODEL_PARENT"','')
    if vcs:
        code=change(code,"SETUP='/usr/eelocal/cadence/xcelium2303hf/.cshrc'","SETUP='/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc'")
        start=code.index("    script='''")
        end=code.index("    (work/'run.csh').write_text(script)",start)
        dut='netlist.v' if gate else 'dut.sv'
        extra=' +define+TETRAMAX +nospecify +notimingcheck' if gate else ''
        lib=' -v "MODEL_PATH" +incdir+"MODEL_PARENT"' if gate else ''
        script='''    script='''+"'''"+'''#!/bin/tcsh -f
source "SETUP_PATH"
if ($status != 0) exit 90
rehash
vcs -ID >& tool_version.log
if ($status != 0) exit 91
vcs -full64 -sverilog'''+extra+''' -top tb testbench.sv reference.sv '''+dut+lib+''' -o simv -l compile.log
set compile_rc = $status
echo $compile_rc > compile.exit
if ($compile_rc != 0) exit $compile_rc
./simv -l simulate.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
'''+"'''.replace('SETUP_PATH',SETUP).replace('MODEL_PATH',MODEL).replace('MODEL_PARENT',str(Path(MODEL).parent))\n"
        code=code[:start]+script+code[end:]
        code=code.replace("(work/'xrun.log')","(work/'simulate.log')")
        code=code.replace("'xrun.log','simulate.exit'","'xrun.log','simulate.log','compile.log','compile.exit','simulate.exit'")
    code=code.replace('Xcelium setup/tcsh unavailable',('VCS' if vcs else 'Xcelium')+' setup/tcsh unavailable')
    code=code.replace('ONE DC NETLIST / XCELIUM; WORK:',selector.upper()+' / SLOT025; WORK:')
    code=code.replace("kind='next96_dc_gatesim'","kind='next96_commercial_single'")
    (folder/'school_sim.py').write_text(code,encoding='utf-8',newline='\n')
    ast.parse(code,feature_version=(3,6))
    for n in ['testbench.sv','reference.sv']:(folder/n).write_bytes((SRC/n).read_bytes())
    dut='netlist.v' if gate else 'dut.sv'
    (folder/dut).write_bytes((DC if gate else SRC/'dut.sv').read_bytes())
    save(folder/'manifest.json',dict(key=key,selector=selector,slot=25,expected_samples=213,netlist_sha256=sha(DC) if gate else None,source_rtl_sha256=sha(SRC/'dut.sv'),source_testbench_sha256=sha(SRC/'testbench.sv'),source_reference_sha256=sha(SRC/'reference.sv'),scope='Unmodified original fixed test; preserve actual counts, no simulator-dependent threshold adjustment; random stream identity not established. No SDF.'))
    names={'school_sim.py','manifest.json','testbench.sv','reference.sv',dut}
    save(folder/'payload-lock.json',{n:sha(folder/n) for n in sorted(names)})
    sp=importlib.util.spec_from_file_location(selector,folder/'school_sim.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
    assert m.verify(folder)['key']==key
    assert m.verdict('Mismatches: 0 in 211 samples',0)['status']=='CHECK_COUNT_DIFFERENT'
    assert m.verdict('Mismatches: 0 in 213 samples',0)['status']=='FIXED_TEST_PASS'
    assert m.verdict('Mismatches: 1 in 213 samples',0)['status']=='FUNCTION_FAIL'
    assert m.verdict('Mismatches: 0 in 213 samples',1)['status']=='TOOL_ERROR'
    assert (folder/'testbench.sv').read_bytes()==(SRC/'testbench.sv').read_bytes()
    assert (folder/'reference.sv').read_bytes()==(SRC/'reference.sv').read_bytes()
    archive=OUT/(key+'.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for n in sorted(names|{'payload-lock.json'}):z.write(folder/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==names|{'payload-lock.json'}
        assert all(z.read(n)==(folder/n).read_bytes() for n in z.namelist())
    shutil.copyfile(archive,SHARED/archive.name)
    catalog.append(dict(selector=selector,key=key,archive=archive.name,sha256=sha(archive),inputs=sorted(names|{'payload-lock.json'}),runner_sha256=sha(folder/'school_sim.py')))
selection=''
for c in catalog:selection+='  '+c['selector']+') archive="'+c['archive']+'"; digest="'+c['sha256']+'" ;;\n'
bootstrap='''#!/usr/bin/env bash
set -eu
case "${1:-}" in
'''+selection+'''  *) echo 'Choose ONE: xcelium-rtl | vcs-rtl | vcs-dc'; exit 2 ;;
esac
share_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$share_dir/$archive" "$digest" "$share_dir" <<'PY_BOOT'
import hashlib,io,os,sys,tempfile,zipfile
from pathlib import Path
blob=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest()!=sys.argv[2]:raise SystemExit('STOP: ZIP hash mismatch')
work=Path(tempfile.mkdtemp(prefix='next96-single-payload-',dir=str(Path.home())))
common={'school_sim.py','manifest.json','testbench.sv','reference.sv','payload-lock.json'}
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    names=set(z.namelist())
    if names not in (common|{'dut.sv'},common|{'netlist.v'}) or len(z.namelist())!=6 or z.testzip() is not None:raise SystemExit('STOP: ZIP members invalid')
    for name in sorted(names):(work/name).write_bytes(z.read(name))
os.execv(sys.executable,[sys.executable,str(work/'school_sim.py'),'run','--return-dir',sys.argv[3]])
PY_BOOT
'''
(OUT/'start_verify25.sh').write_text(bootstrap,encoding='utf-8',newline='\n')
shutil.copyfile(OUT/'start_verify25.sh',SHARED/'start_verify25.sh')
save(OUT/'catalog.json',catalog)
save(OUT/'offline-verification.json',dict(status='PASS',cases=3,python36_parses=3,package_verifies=3,verdict_checks=12,unmodified_tb_reference_pairs=3,zip_byte_roundtrips=3,process_runner='Unchanged bounded() from already tested DC-Xcelium wrapper',model_calls=0,commercial_tool_calls=0,school_execution='PENDING_USER_MANUAL_COMMANDS'))
print(json.dumps(catalog,indent=2))
