"""Export individual manual VDI checks, then import evidence. No SSH or batch jobs."""
import argparse
import json
from pathlib import Path
import re
import shutil
import uuid

import batch
import rtl_lab as lab


def script(backend,nonce):
    header='''#!/bin/tcsh -f
# Run ONE case on the logged-in ECE VDI host. No scheduler or SSH required.
cd "$0:h"
rm -f verdict.txt compile.exit simulate.exit
'''
    if backend=='vcs':
        return header+f'''if (! $?VCS_SETUP) setenv VCS_SETUP /usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc
source "$VCS_SETUP"
if ($status != 0) exit 2
rehash
vcs -ID >& tool_version.log
# Read the harness timescale before modules without an explicit directive.
vcs -full64 -sverilog -top tb testbench.sv dut.sv -o simv -l compile.log
set compile_rc = $status
echo $compile_rc > compile.exit
if ($compile_rc != 0) exit $compile_rc
./simv +nonce={nonce} -l simulate.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
'''
    return header+f'''if (! $?XCELIUM_SETUP) setenv XCELIUM_SETUP /usr/eelocal/cadence/xcelium2303hf/.cshrc
source "$XCELIUM_SETUP"
if ($status != 0) exit 2
rehash
xrun -version >& tool_version.log
xrun -64bit -sv -top tb dut.sv testbench.sv +nonce={nonce} -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
'''


def export(run,output,backend,jobs):
    if output.exists() and any(output.iterdir()):raise ValueError('Choose an empty export directory')
    plan=batch.read(run/'plan.json'); selected=[]
    ids=set(jobs.split(','))
    known={j['id'] for j in plan['jobs']}
    if not ids or ids-known:raise ValueError('Provide exact comma-separated job IDs from summary.json')
    for job in plan['jobs']:
        if job['id'] not in ids:continue
        row=batch.latest(run,job)
        if not row:raise ValueError('Job has no result: '+job['id'])
        folder=run/row['directory'];spec=next(s for s in plan['tasks'] if s['id']==job['task'])
        if not (folder/'dut.sv').is_file():raise ValueError('No extracted RTL: '+job['id'])
        # Enforce the same source constraints and original run hashes.
        lab.extract_rtl((folder/'dut.sv').read_text(encoding='utf-8'),spec['module'])
        files={'dut.sv':row['rtl_sha256'],'testbench.sv':spec['tb_sha256'],**spec.get('assets',{})}
        for name,expected in files.items():
            if lab.digest((folder/name).read_bytes())!=expected:raise ValueError('Source evidence changed: '+name)
        selected.append((job,row,spec,folder,files))
    output.mkdir(parents=True,exist_ok=True)
    package=dict(schema=1,backend=backend,created_utc=lab.utc(),cases=[],
        policy='Manual single-case VDI checks only. ECE shared VDI has no SSH or supported EDA batch service.')
    for job,row,spec,folder,files in selected:
        case=output/job['id'];case.mkdir();nonce=uuid.uuid4().hex
        for name in files:shutil.copyfile(folder/name,case/name)
        meta=dict(job_id=job['id'],task=spec['id'],backend=backend,checks=spec['checks'],nonce=nonce,hashes=files,
                  original_mode=row['mode'],original_status=row['status'])
        batch.atomic(case/'case.json',meta)
        (case/('run_'+backend+'.csh')).write_text(script(backend,nonce),encoding='utf-8',newline='\n')
        if backend=='xcelium':(case/'run.tcl').write_text('run\nexit\n',encoding='ascii')
        package['cases'].append(meta)
    batch.atomic(output/'package.json',package)
    (output/'README.txt').write_text(
        '学校 VDI 手动复核包。通过共享文件夹复制到 Linux 家目录。\n'
        '每次进入一个案例目录，执行：tcsh run_'+backend+'.csh\n'
        '不要在共享 VDI 上循环批量执行。脚本路径来自已有资料，可用 VCS_SETUP / XCELIUM_SETUP 覆盖。\n'
        '将完整案例目录复制回本机，保留源码、向量、退出码和日志。\n'
        '本机导入：python school_bridge.py import --package 原始导出目录 --returned 回传目录\n'
        'VCS/Xcelium 脚本尚需在学校对应版本上实际验证。本机离线验收不等于商业工具验收。\n',encoding='utf-8')
    print('Manual package: '+str(output))


def import_results(package_dir,returned):
    package=batch.read(package_dir/'package.json');rows=[]
    for meta in package['cases']:
        folder=returned/meta['job_id']
        row=dict(job_id=meta['job_id'],task=meta['task'],backend=meta['backend'],status='NOT_RUN',message='No returned evidence')
        try:
            for name,expected in meta['hashes'].items():
                if not (folder/name).is_file() or lab.digest((folder/name).read_bytes())!=expected:
                    raise ValueError('Missing or changed source: '+name)
            log_names=['compile.log','simulate.log'] if meta['backend']=='vcs' else ['xrun.log']
            logs='\n'.join((folder/n).read_text(encoding='utf-8',errors='replace') for n in log_names if (folder/n).is_file())
            if re.search(r'NOLICN|LMC-10901|Unable to checkout|License checkout failed',logs,re.I):
                row.update(status='ENV_ERROR',message='Commercial license unavailable')
            elif (folder/'compile.exit').exists() and int((folder/'compile.exit').read_text().strip())!=0:
                row.update(status='COMPILE_FAIL',message='Commercial compilation returned nonzero')
            elif (folder/'simulate.exit').exists():
                if not (folder/'tool_version.log').is_file() or not all((folder/n).is_file() for n in log_names):
                    raise ValueError('Returned evidence lacks version or tool logs')
                result={'timeout':False,'output_limit':False,'returncode':int((folder/'simulate.exit').read_text().strip())}
                receipt=(folder/'verdict.txt').read_text() if (folder/'verdict.txt').exists() else ''
                row['status'],row['message']=lab.judge_simulation(result,receipt,meta['checks'],meta['nonce'])
                row['tool_version']=(folder/'tool_version.log').read_text(encoding='utf-8',errors='replace') if (folder/'tool_version.log').exists() else None
                row['evidence_hashes']={n:lab.digest((folder/n).read_bytes()) for n in log_names+['simulate.exit','verdict.txt','tool_version.log'] if (folder/n).is_file()}
        except (OSError,ValueError) as exc:row.update(status='EVIDENCE_ERROR',message=str(exc))
        rows.append(row)
    batch.atomic(package_dir/'commercial_results.json',dict(backend=package['backend'],imported_utc=lab.utc(),results=rows,
        note='Imported user-run evidence; source hashes, nonce, check count and simulator exit checked. Manual tool failures may need log review.'))
    print(json.dumps(rows,ensure_ascii=False,indent=2))
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    e=sub.add_parser('export');e.add_argument('--run-dir',required=True);e.add_argument('--out',required=True)
    e.add_argument('--backend',choices=['vcs','xcelium'],required=True);e.add_argument('--jobs',required=True)
    i=sub.add_parser('import');i.add_argument('--package',required=True);i.add_argument('--returned',required=True)
    a=p.parse_args()
    try:
        if a.command=='export':export(Path(a.run_dir).resolve(),Path(a.out).resolve(),a.backend,a.jobs)
        else:import_results(Path(a.package).resolve(),Path(a.returned).resolve())
    except (ValueError,OSError,KeyError) as exc:print('ERROR: '+str(exc));return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
