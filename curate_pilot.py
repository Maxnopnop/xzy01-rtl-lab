"""Export an allowlisted, shareable evidence snapshot; never copy account/raw CLI logs."""
import argparse
from pathlib import Path
import shutil

import batch
import pilot
import rtl_lab as lab


def curate(run, out):
    summary=pilot.report(run)
    if not summary['generation_complete'] or not summary['synthesis_complete']:
        raise ValueError('Only curate a completed pilot and synthesis review')
    if out.exists():raise ValueError('Use a new evidence directory')
    out.mkdir(parents=True)
    for name in ('pilot-summary.json','pilot-summary.csv','pilot-report.html'):
        shutil.copyfile(run/name,out/name)
    plan=batch.read(run/'pilot.json');models=[]
    for item in plan['runs']:
        folder=run/item['directory'];bp=batch.read(folder/'plan.json');env=batch.read(folder/'environment.json')
        keep=('mode','model','codex_reasoning','api_timeout','compile_timeout','sim_timeout','temperature','seed','synthesis')
        synth_env=batch.read(folder/'synthesis-review/environment.json')
        tool={k:v for k,v in synth_env['tool'].items() if k!='path'}
        models.append(dict(model=item['model'],config={k:bp['config'][k] for k in keep},
            source_hashes=bp['source_hashes'],original_plan_sha256=lab.digest((folder/'plan.json').read_bytes()),
            tools={k:{key:value for key,value in v.items() if key!='path'} for k,v in env['tools'].items()},
            codex_sha256=env['codex']['sha256'],synthesis_tool=tool,
            synthesis_source_hashes={k:v for k,v in synth_env.items() if k not in ('tool',)},
            python=env['python'],platform=env['platform']))
        for job in bp['jobs']:
            result=batch.latest(folder,job)
            source=folder/result['directory'];dest=out/'generated'/item['directory']/f'sample_{job["sample"]:03d}'
            dest.mkdir(parents=True,exist_ok=True)
            if result.get('rtl_sha256'):
                shutil.copyfile(source/'dut.sv',dest/(job['task']+'.sv'))
            # Save exact outgoing prompt, with no CLI events or auth metadata.
            prompts=out/'prompts';prompts.mkdir(exist_ok=True)
            data=(source/'codex_prompt.txt').read_bytes()
            prompt=prompts/(job['task']+'.txt')
            if prompt.exists() and prompt.read_bytes()!=data:raise ValueError('Model prompts differ')
            prompt.write_bytes(data)
            review=batch.read(folder/'synthesis-review'/job['id']/'result.json')
            fields=('task','sample','requested_model','status','stage','message','usage','generation_seconds',
                    'rtl_sha256','testbench_sha256','expected_checks','sampling','model_identity_basis',
                    'codex_generation_success','tools_used','receipt_nonce')
            record={k:result[k] for k in fields if k in result}
            record['synthesis']={k:v for k,v in review.items() if k!='directory'}
            batch.atomic(dest/(job['task']+'.result.json'),record)
            if result['status']=='COMPILE_FAIL':
                text=(source/'compile.stderr.log').read_text(encoding='utf-8')
                text=text.replace(str(run),'<run>')
                (dest/(job['task']+'.compile.txt')).write_bytes((text.rstrip()+'\n').encode('utf-8'))
    batch.atomic(out/'experiment.json',dict(config=plan['config'],models=models,
        original_pilot_sha256=lab.digest((run/'pilot.json').read_bytes()),
        note='Allowlisted metadata and generated RTL only. Raw account/CLI logs remain local.'))
    print(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',required=True);p.add_argument('--out',required=True)
    args=p.parse_args()
    try:curate(Path(args.run_dir).resolve(),Path(args.out).resolve())
    except (OSError,ValueError,KeyError) as exc:p.exit(2,'ERROR: '+str(exc)+'\n')
