"""Independent generic Yosys synthesis stage; never a technology/PPA claim.

Run natively on Linux/WSL (or Windows with a native Yosys installation).
Keeping the whole worker inside WSL lets the existing process-group timeout
clean up Yosys and ABC; killing a Windows wsl.exe is not a cleanup strategy.
"""
import json
import re
import shutil
import argparse
from collections import Counter
from pathlib import Path

import rtl_lab as lab


def inspect(args, folder):
    executable = shutil.which(getattr(args, 'yosys', None) or 'yosys')
    if not executable:
        raise ValueError('Yosys not found. Run the complete batch inside WSL/Linux or specify native --yosys.')
    result = lab.run_process([executable, '-V'], folder, 10)
    if result['returncode'] or result['timeout'] or result['output_limit']:
        raise ValueError('Yosys version check failed')
    return dict(path=str(Path(executable).resolve()), version=result['stdout'].strip(),
                sha256=lab.digest(Path(executable).read_bytes()), flow='generic-synth-noabc-v1')


def evaluate(folder, spec, tool, timeout):
    top = spec['module']
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', top):
        raise ValueError('Invalid synthesis top')
    # Check before optimization so conflicting drivers are not optimized away.
    # No ABC/liberty/technology mapping: reproducible generic logic statistics.
    script = ('read_verilog -sv dut.sv\n'
              f'hierarchy -check -top {top}\n'
              'proc\ncheck -assert\n'
              f'synth -noabc -top {top}\n'
              'check -assert\ntee -o synthesis-stat.json stat -json\n'
              'write_json synthesis-netlist.json\n')
    (folder/'synthesis.ys').write_text(script, encoding='utf-8')
    result = lab.run_process([tool['path'], '-T', '-s', 'synthesis.ys'], folder, timeout)
    lab.save_process(folder, 'synthesis', result, '')
    row = dict(backend='yosys', flow=tool['flow'], elapsed_seconds=result['elapsed_seconds'],
               statistics_kind='generic cells, not silicon area/timing/power')
    if result['timeout']:
        return dict(row, status='SYNTH_TIMEOUT', message='Synthesis process group exceeded wall timeout')
    if result['output_limit'] or result['returncode'] != 0:
        return dict(row, status='SYNTH_FAIL', message='See synthesis logs; no valid netlist')
    try:
        stats = json.loads((folder/'synthesis-stat.json').read_text(encoding='utf-8'))
        module = stats['modules']['\\'+top]
        cells = module['num_cells_by_type']
        # Latches may synthesize legally. Flag them for review instead of
        # silently interpreting generic synthesis success as intended behavior.
        latches = sum(n for name,n in cells.items() if 'LATCH' in name.upper())
        return dict(row, status='SYNTH_PASS', generic_cells=module['num_cells'],
                    cell_types=cells, latch_cells=latches,
                    netlist_sha256=lab.digest((folder/'synthesis-netlist.json').read_bytes()),
                    message='Generic synthesis and structural checks passed')
    except (OSError, ValueError, KeyError):
        return dict(row, status='SYNTH_ERROR', message='Missing or invalid synthesis artifacts')


def review(run, yosys=None, timeout=60):
    """Synthesize retained RTL without regenerating it or altering simulation evidence."""
    import batch
    from types import SimpleNamespace
    run=Path(run).resolve();plan=batch.read(run/'plan.json')
    with batch.lock(run):
        if any(batch.latest(run,j) is None for j in plan['jobs']):
            raise ValueError('Finish generation before synthesis review')
        root=run/'synthesis-review';root.mkdir(exist_ok=True)
        tool=inspect(SimpleNamespace(yosys=yosys),root)
        identity=dict(tool=tool,timeout=timeout,source=lab.digest(Path(__file__).read_bytes()),
                      process_runner=lab.digest(Path(lab.__file__).read_bytes()),
                      plan_sha256=lab.digest((run/'plan.json').read_bytes()))
        env=root/'environment.json'
        if env.exists() and batch.read(env)!=identity:
            raise ValueError('Review code, tool or plan changed; preserve this review and use a new run')
        batch.atomic(env,identity)
        rows=[]
        for job in plan['jobs']:
            source=run/'jobs'/job['id']/'result.json';sim=batch.read(source)
            binding=dict(job_id=job['id'],source_result_sha256=lab.digest(source.read_bytes()),
                         rtl_sha256=sim.get('rtl_sha256'),simulation_status=sim['status'])
            if sim.get('rtl_sha256'):
                source_dir=(run/sim['directory']).resolve()
                if not source_dir.is_relative_to(run):raise ValueError('Invalid source directory')
                data=(source_dir/'dut.sv').read_bytes()
                if lab.digest(data)!=sim['rtl_sha256']:raise ValueError('RTL hash mismatch')
            dest=root/job['id'];dest.mkdir(exist_ok=True)
            output=dest/'result.json'
            if output.exists():
                row=batch.read(output)
                if any(row[k]!=v for k,v in binding.items()):raise ValueError('Original evidence changed')
            elif not sim.get('rtl_sha256'):
                row=dict(binding,status='NOT_RUN',message='No accepted RTL to synthesize')
            else:
                spec=next(s for s in plan['tasks'] if s['id']==job['task'])
                lab.extract_rtl(data.decode('utf-8'),spec['module'])
                # Preserve any interrupted artifacts as a distinct attempt.
                attempt=dest/f'attempt_{len(list(dest.glob("attempt_*")))+1:03d}';attempt.mkdir()
                (attempt/'dut.sv').write_bytes(data)
                row=dict(binding,**evaluate(attempt,spec,tool,timeout),directory=str(attempt.relative_to(root)))
            batch.atomic(output,row);rows.append(row)
            print(job['id']+': '+row['status'],flush=True)
        summary=dict(schema=1,kind='SYNTHESIS_REPLAY_OF_RETAINED_RTL',new_model_calls=0,
                     counts=dict(Counter(r['status'] for r in rows)),planned=len(plan['jobs']),results=rows,
                     joint_passes=sum(r['status']=='SYNTH_PASS' and r['simulation_status']=='PASS' for r in rows))
        batch.atomic(root/'summary.json',summary)
        return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',required=True);parser.add_argument('--yosys')
    parser.add_argument('--timeout',type=lab.positive,default=60)
    args=parser.parse_args()
    try:
        summary=review(args.run_dir,args.yosys,args.timeout)
        print(json.dumps({k:v for k,v in summary.items() if k!='results'}))
        raise SystemExit(0 if summary['counts']=={'SYNTH_PASS':summary['planned']} else 1)
    except (OSError,ValueError,lab.LabError) as exc:
        parser.exit(2,'ERROR: '+str(exc)+'\n')
