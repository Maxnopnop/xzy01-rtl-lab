"""Local manual school packaging and verified import. Never starts school tools."""
import json
from pathlib import Path
import re
import shutil
import stat
import uuid
import zipfile
import console_bridge_v3 as b

def deps():
    for name,h in b.read(b.ROOT/'console_dependencies.json').items():
        b.require(b.sha(b.ROOT/name)==h,'冻结依赖变化: '+name)

def pack(row,tool,shared,profile=None,sdc=None):
    deps()
    b.require(tool in ('dc','genus','vcs','xcelium'),'未知学校工具')
    shared=Path(shared).resolve()
    b.require(shared.is_dir(),'请先选择已映射的共享目录')
    source=Path(row['job_dir']);result_path=Path(row['result_path'])
    b.require(result_path.is_file() and (source/'dut.sv').is_file(),'此槽无保存 RTL/结果')
    result=b.read(result_path)
    provenance=b.validate_saved_inputs(row)
    checks=result.get('receipt')
    expected=checks[0][1] if checks else row.get('expected_checks')
    if tool in ('vcs','xcelium'):b.require(type(expected) is int and expected>0,'缺原检查数，不能猜测学校评分阈值')
    if tool in ('dc','genus'):
        import ece_synth_common as c
        b.require(profile is not None and sdc is not None,'选择已审核 SDC 与对应工具配置')
        profile=dict(profile,sdc_file='constraints.sdc')
        b.require(not c.validate_profile(tool,profile),'库/工艺角/约束审核配置不完整')
    key='console-'+uuid.uuid4().hex[:16]
    folder=b.STATE/'school'/key
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'dut.sv').write_bytes((source/'dut.sv').read_bytes())
    shutil.copyfile(b.ROOT/'console_school_runner_v3.py',folder/'console_school_runner_v3.py')
    if tool in ('dc','genus'):
        (folder/'constraints.sdc').write_bytes(Path(sdc).read_bytes())
        nonce=uuid.uuid4().hex
        job=dict(schema=1,package_id=key,tool=tool,top=row.get('top','TopModule'),job_id=row['id'],source_result_sha256=b.sha(result_path),source_plan_sha256=row.get('request_sha256'),rtl_sha256=b.sha(source/'dut.sv'),sdc_sha256=b.sha(folder/'constraints.sdc'),original_simulation=result['status'],nonce=nonce,profile=profile,expected_tool=c.TOOLS[tool])
        b.save(folder/'job.json',job)
        (folder/'synthesis.tcl').write_text(c.tcl(tool,job['top'],profile,nonce),encoding='utf-8',newline='\n')
        (folder/'launch.csh').write_text(c.launcher(tool),encoding='utf-8',newline='\n')
        for name in ('ece_synth_common.py','ece_synth_school.py'):shutil.copyfile(b.ROOT/name,folder/name)
        b.save(folder/'payload-lock.json',{n:b.sha(folder/n) for n in sorted(c.INPUTS)})
        c.verify(folder)
    else:
        for name in ('testbench.sv','reference.sv'):(folder/name).write_bytes((source/name).read_bytes())
        setup='/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc' if tool=='vcs' else '/usr/eelocal/cadence/xcelium2303hf/.cshrc'
        commands=('vcs -ID >& tool_version.log\nvcs -full64 -sverilog -top tb testbench.sv reference.sv dut.sv -o simv -l compile.log\nif ($status != 0) exit 92\n./simv -l simulate.log' if tool=='vcs' else 'xrun -version >& tool_version.log\nxrun -64bit -sv -top tb testbench.sv reference.sv dut.sv -input run.tcl -l simulate.log')
        (folder/'run.csh').write_text('#!/bin/tcsh -f\nsource "'+setup+'"\nif ($status != 0) exit 90\nrehash\n'+commands+'\nset rc = $status\necho $rc > simulate.exit\nexit $rc\n',encoding='utf-8',newline='\n')
        (folder/'run.tcl').write_text('run\nexit\n',encoding='utf-8')
    inputs={p.name:b.sha(p) for p in folder.iterdir() if p.is_file()}
    manifest=dict(schema=1,key=key,tool=tool,slot=row['id'],dataset=row['dataset'],expected_checks=expected,source_result_sha256=b.sha(result_path),source_rtl_sha256=b.sha(source/'dut.sv'),provenance=provenance,inputs=inputs)
    b.save(folder/'console-manifest.json',manifest)
    # The bootstrap verifies the manifest before executing any packaged Python.
    mh=b.sha(folder/'console-manifest.json')
    script='#!/usr/bin/env bash\nset -eu\ncd -- "$(dirname -- "$0")"\nprintf "%s  %s\\n" "'+mh+'" console-manifest.json | sha256sum -c -\n'
    script+='python3 - <<\'PY\'\nimport hashlib,json\nfrom pathlib import Path\nm=json.loads(Path("console-manifest.json").read_text())\nfor n,h in m["inputs"].items():\n if Path(n).name!=n or hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h: raise SystemExit("STOP: package hash mismatch")\nPY\nexec python3 console_school_runner_v3.py "$@"\n'
    (folder/'run-one.sh').write_text(script,encoding='utf-8',newline='\n')
    check=script[:script.index('exec python3 console_school_runner_v3.py')]
    (folder/'check-share.sh').write_text(check+'echo "SHARED PACKAGE VERIFIED; no EDA started"\n',encoding='utf-8',newline='\n')
    (folder/'ship-only.sh').write_text(check+'exec python3 console_school_runner_v3.py ship "$1"\n',encoding='utf-8',newline='\n')
    shutil.copyfile(b.ROOT/'console_stage_v3.py',folder/'console_stage_v3.py')
    files={p.name:b.sha(p) for p in folder.iterdir()}
    b.save(folder/'transfer-lock.json',files)
    archive=shared/(key+'.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.iterdir()):z.write(p,p.name)
    # Bootstrap copies the ZIP into HOME before reading/extracting it. Only stdlib before verification.
    stage_name='stage-'+key+'.sh'
    stage_script='#!/usr/bin/env bash\nset -eu\nshare=$(cd -- "$(dirname -- "$0")" && pwd)\nmkdir -p "$HOME/xzy01-console-v3/archives"\narchive="$HOME/xzy01-console-v3/archives/'+key+'.zip"\ntimeout 60s cp -- "$share/'+key+'.zip" "$archive"\nprintf "%s  %s\\n" "'+b.sha(archive)+'" "$archive" | sha256sum -c -\npython3 - "$archive" <<\'PY\'\nimport hashlib,sys,zipfile\nfrom pathlib import Path\np=Path(sys.argv[1])\nif hashlib.sha256(p.read_bytes()).hexdigest()!="'+b.sha(archive)+'":raise SystemExit("ZIP changed")\nwith zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")\nif hashlib.sha256(code).hexdigest()!="'+files['console_stage_v3.py']+'":raise SystemExit("Stage code changed")\nns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)\nns["stage"](p,"'+b.sha(archive)+'")\nPY\n'
    with (shared/stage_name).open('x',encoding='utf-8',newline='\n') as f:f.write(stage_script)
    record=dict(key=key,local=str(folder),shared=str(shared),manifest_sha256=mh,files=files,archive=archive.name,archive_sha256=b.sha(archive),stage_script=stage_name,stage_sha256=b.sha(shared/stage_name),transport='HOME_ZIP_FLAT_V3')
    b.save(b.STATE/'school'/f'{key}.json',record)
    return record

def command(record,action='run'):
    b.require(record.get('transport')=='HOME_ZIP_FLAT_V3','旧共享直跑包仅由v2入口处理')
    b.require(b.sha(Path(record['shared'])/record['archive'])==record['archive_sha256'],'共享ZIP变化')
    b.require(b.sha(Path(record['shared'])/record['stage_script'])==record['stage_sha256'],'暂存脚本变化')
    key=b.safe_id(record['key']);root='"$HOME/xzy01-console-v3/'+key+'/'
    stage='printf "%s  %s\\n" "'+record['stage_sha256']+'" "$HOME/tsclient/FYP/'+record['stage_script']+'" | sha256sum -c - && bash "$HOME/tsclient/FYP/'+record['stage_script']+'"'
    if action=='check':return stage
    if action=='ship':return 'bash '+root+'ship-only.sh" "$HOME/tsclient/FYP"'
    b.require(action=='run','Unknown action')
    return stage+' && bash '+root+'run-one.sh" run "$HOME/tsclient/FYP"'

def collect(record,sidecar):
    sidecar=Path(sidecar);meta=b.read(sidecar)
    b.require(meta['key']==record['key'] and meta['manifest_sha256']==record['manifest_sha256'],'回传来源不匹配')
    archive=sidecar.with_suffix('.zip') if sidecar.name=='return-'+record['key']+'.json' else sidecar.parent/'console-return.zip'
    b.require(b.sha(archive)==meta['archive_sha256'],'回传 ZIP hash 不匹配')
    original=Path(record['local']);manifest=b.read(original/'console-manifest.json')
    allowed=set(manifest['inputs'])|{'console-manifest.json','console-result.json','launcher.log','simulate.log','compile.log','tool_version.log','simulate.exit','execution.json','doctor.json','tool.log','tool_path.txt','receipt.txt','outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt','reports/check_design.rpt','reports/constraints.rpt'}
    with zipfile.ZipFile(archive) as z:
        members=z.infolist()
        b.require(len({i.filename for i in members})==len(members) and sum(i.file_size for i in members)<=100*1024**2,'重复成员或回传过大')
        b.require(all(i.filename in allowed and not stat.S_ISLNK(i.external_attr>>16) for i in members),'回传成员不在白名单')
        b.require(z.testzip() is None,'ZIP CRC 错误')
        for name,h in manifest['inputs'].items():b.require(b.digest(z.read(name))==h,'原始输入被修改')
        b.require(b.digest(z.read('console-manifest.json'))==record['manifest_sha256'],'清单改变')
        reported=json.loads(z.read('console-result.json'))
        b.require(reported['key']==record['key'] and reported['manifest_sha256']==record['manifest_sha256'],'结果来源不符')
        if manifest['tool'] in ('vcs','xcelium'):
            code=int(z.read('simulate.exit')) if 'simulate.exit' in z.namelist() else reported.get('returncode')
            text=z.read('simulate.log').decode('utf-8',errors='replace') if 'simulate.log' in z.namelist() else ''
            checked=b.simulation_verdict(text,code,manifest['expected_checks'])
            if reported['status'] not in ('TIMEOUT','RESOURCE_LIMIT','ENVIRONMENT_ERROR','EVIDENCE_ERROR'):
                b.require(checked['fixed_test']==reported['status'],'学校回执与原日志不一致')
                for field in ('samples','mismatches'):
                    if field in reported:b.require(reported[field]==checked.get(field),'回传计数与日志不一致')
        elif reported['status']=='COMPLETED_REVIEW_REQUIRED':
            import ece_synth_common as c
            job=json.loads(z.read('job.json'));execution=json.loads(z.read('execution.json'))
            b.require(execution.get('returncode')==0 and execution.get('nonce')==job['nonce'],'综合执行回执不符')
            b.require(z.read('receipt.txt').decode().strip()=='XZY01_SYNTH_V1 '+job['nonce']+' COMPLETE','综合完成标记不符')
            b.require(all(n in z.namelist() and z.getinfo(n).file_size>0 for n in c.REQUIRED),'综合产物不全')
        destination=b.STATE/'school-returned'/meta['archive_sha256']
        if not destination.exists():
            destination.mkdir(parents=True)
            for item in members:
                p=b.inside(destination,item.filename);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(item))
            shutil.copyfile(archive,destination/'original-return.zip')
            b.save(destination/'import.json',dict(reported,archive_sha256=meta['archive_sha256'],verified=True))
    return b.read(destination/'import.json')
