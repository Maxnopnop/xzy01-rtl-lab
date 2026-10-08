"""Offline re-simulation of historical generated RTL; zero new model calls."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import batch
from backends import IcarusBackend
import ece_workflow as workflow
import rtl_lab as lab


def replay(output, workers=4):
    if output.exists(): raise ValueError('Use a new replay directory')
    output.mkdir(parents=True)
    args=SimpleNamespace(iverilog=None,vvp=None,compile_timeout=15,sim_timeout=15)
    tools=lab.inspect_tools(args,output); candidates=[]; excluded=[]
    for entry in workflow.history():
        run=workflow.ROOT/entry['run']; plan=workflow.read(run/'plan.json')
        for job in plan['jobs']:
            row=batch.latest(run,job)
            if not row or not row.get('rtl_sha256'):
                excluded.append(dict(run=entry['run'],job_id=job['id'],reason='No retained RTL; infrastructure/pending, not replayed'))
                continue
            spec=next(s for s in plan['tasks'] if s['id']==job['task'])
            source=run/row['directory']
            files={'dut.sv':row['rtl_sha256'],'testbench.sv':spec['tb_sha256'],**spec.get('assets',{})}
            for name,expected in files.items():
                if lab.digest((source/name).read_bytes())!=expected: raise ValueError('Historical source changed: '+str(source/name))
            key=entry['run'].replace('/','__')+'__'+job['id']
            target=output/'jobs'/key;target.mkdir(parents=True)
            for name in files:shutil.copyfile(source/name,target/name)
            candidates.append((target,spec,dict(run=entry['run'],job_id=job['id'],task=job['task'],
                expected=row['status'],source_hashes=files)))
    workflow.saved(output/'replay-plan.json',dict(new_model_calls=0,workers=workers,planned=len(candidates),excluded=excluded,
        source_hashes={n:lab.digest((workflow.ROOT/n).read_bytes()) for n in ['ece_replay.py','ece_workflow.py']+batch.CODE_FILES}))
    def one(item):
        target,spec,meta=item
        row=dict(meta,**IcarusBackend().evaluate(target,spec,tools,args))
        row['consistent']=row['status']==row['expected']
        workflow.saved(target/'replay-result.json',row)
        return row
    rows=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending=[pool.submit(one,item) for item in candidates]
        for future in as_completed(pending):
            rows.append(future.result())
            if len(rows)%20==0: print('Replay '+str(len(rows))+'/'+str(len(candidates)),flush=True)
    rows.sort(key=lambda r:(r['run'],r['job_id']))
    summary=dict(new_model_calls=0,planned=len(candidates),completed=len(rows),
        counts=dict(Counter(r['status'] for r in rows)),consistent=sum(r['consistent'] for r in rows),
        unexpected=[r for r in rows if not r['consistent']],excluded=excluded,results=rows,
        limitation='Replayed historical outputs are not new model samples; expected functional/compile failures are retained.')
    workflow.saved(output/'summary.json',summary)
    with (output/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['run','job_id','task','expected','status','consistent'];writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('results','excluded','unexpected')},indent=2))
    return 0 if not summary['unexpected'] else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    if not 1<=args.workers<=8: p.error('workers must be 1..8')
    try:return replay(Path(args.out).resolve(),args.workers)
    except (ValueError,OSError,KeyError,lab.LabError) as exc:print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
