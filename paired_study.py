"""One-call paired feedback study, with fixed artifacts shared across conditions."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import csv
import html
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import backends
import batch
import codex_adapter
import fsm_checks
import fsm_ir
import fsm_study
import paired_bank as bank
import rtl_lab as lab

MODELS = ('gpt-5.6-sol','gpt-5.6-terra')
ARMS = ('control','feedback')


def identity():
    return {name:lab.digest((batch.ROOT/name).read_bytes()) for name in
            (*batch.CODE_FILES,'fsm_ir.py','fsm_checks.py','fsm_study.py','paired_bank.py','paired_study.py',
             'benchmarks/paired-v1/bank-lock.json')}


def init(run, stage, mode='codex', repeats=2, previous=None):
    if run.exists() and any(run.iterdir()): raise ValueError('Choose an empty run directory')
    if stage not in ('A','B') or not 1<=repeats<=2: raise ValueError('Invalid stage/repeats')
    data=bank.load(); cases=[c for c in data['cases'] if c['stage']==stage]
    tasks=[s for s in data['tasks'] if s['id'] in {c['task'] for c in cases}]
    gate=None
    if stage=='B' and mode=='codex':
        if previous is None: raise ValueError('Stage B requires the completed Stage A run')
        earlier=report(previous); prior=read_plan(previous)
        if prior['stage']!='A' or prior['config']['mode']!='codex' or prior['config']['repeats']!=2:
            raise ValueError('Stage A configuration mismatch')
        if earlier['pending'] or earlier['infra_failures'] or earlier['checker_inconsistencies'] or earlier['real_generations']!=32:
            raise ValueError('Stage A reliability gate not met; outcome effectiveness is not part of this gate')
        gate=dict(stage_a_plan_sha256=lab.digest((previous/'plan.json').read_bytes()),
                  stage_a_summary_sha256=lab.digest((previous/'summary.json').read_bytes()),
                  reserved_calls=earlier['model_call_reservations'],total_campaign_cap=96)
    jobs=[]
    for sample in range(1,repeats+1):
        for ci,case in enumerate(cases):
            for mi,model in enumerate(MODELS,1):
                order=ARMS if (ci+mi+sample)%2==0 else ARMS[::-1]
                pair=f'm{mi:02d}__{case["id"]}__s{sample:03d}'
                for arm in order:
                    jobs.append(dict(id=pair+'__'+arm,pair_id=pair,task=case['task'],case=case['id'],model=model,arm=arm,sample=sample))
    config=dict(mode=mode,repeats=repeats,api_timeout=180,compile_timeout=15,sim_timeout=10,
                codex_executable=None,codex_reasoning='low',iverilog=None,vvp=None,synthesis='none')
    run.mkdir(parents=True)
    plan=dict(schema=2,kind='PAIRED_FIXED_IR_REPAIR_V1',stage=stage,created_utc=lab.utc(),
              config=config,jobs=jobs,tasks=tasks,cases=cases,source_hashes=identity(),
              max_calls=len(jobs) if mode=='codex' else 0,expansion_gate=gate,
              fixture_cost_note='Shared initial IRs are retained or deliberately injected, not freshly generated. One new turn per branch; historical generation costs are not zeroed.')
    batch.atomic(run/'plan.json',plan)
    batch.atomic(run/'plan-lock.json',dict(sha256=lab.digest((run/'plan.json').read_bytes())))
    report(run); print(f"Stage {stage}: {len(jobs)} samples / {plan['max_calls']} new-turn cap")


def read_plan(run, verify=False):
    if lab.digest((run/'plan.json').read_bytes())!=batch.read(run/'plan-lock.json')['sha256']:
        raise ValueError('Immutable plan changed')
    plan=batch.read(run/'plan.json')
    if verify:
        bank.load()
        if plan['source_hashes']!=identity(): raise ValueError('Source changed; start a new experiment')
    return plan


def prompt(spec, raw, arm):
    common=(lab.SYSTEM_PROMPT+'\n\n'+spec['spec']+'\n\n'+fsm_study.STYLE+
            '\n\nPublic specification examples shared across conditions:\n'+json.dumps(spec['public_contract'],indent=2)+
            '\n\nCandidate intermediate state table (may contain mistakes):\n'+raw+
            '\n\nImplement the specification. You may correct the candidate table while producing RTL. '
            'There is no extra repair turn. Return only the specified RTL module.\n')
    if arm=='feedback':
        common+='\nExecutable results on the already-public contract:\n'+json.dumps(bank.feedback(raw,spec['public_contract']),indent=2)+'\n'
    return common+'\n'+fsm_study.NO_TOOLS


def judge(folder,spec,rtl,raw,tools,args):
    reference=fsm_ir.parse((bank.ROOT/spec['id']/'reference.json').read_text(encoding='utf-8'))
    candidate=fsm_ir.parse(raw); diagnosis=fsm_ir.product_check(candidate,reference)
    row=dict(ir_diagnosis=diagnosis,public_check=bank.feedback(raw,spec['public_contract']),ir_rtl=dict(status='NOT_RUN'))
    try:
        lab.write_text(folder/'dut.sv',lab.extract_rtl(rtl,spec['module']))
        row['rtl_sha256']=lab.digest((folder/'dut.sv').read_bytes())
        source=bank.ROOT/spec['id']
        for name,expected in {'testbench.sv':spec['tb_sha256'],**spec['assets']}.items():
            data=(source/name).read_bytes()
            if lab.digest(data)!=expected: raise ValueError('Judge data changed')
            (folder/name).write_bytes(data)
        row.update(backends.IcarusBackend().evaluate(folder,spec,tools,args))
        inputs=batch.read(source/'inputs.json')
        for label,ir in [('ir_rtl',candidate),('spec_diagnostic',reference)]:
            comparison=folder/label; comparison.mkdir()
            (comparison/'dut.sv').write_bytes((folder/'dut.sv').read_bytes())
            binding=fsm_checks.write_agreement_test(comparison,spec,ir,inputs,spec['ports'])
            row[label]=dict(binding,**backends.IcarusBackend().evaluate(comparison,binding,tools,args))
            row[label]['mismatches']=fsm_checks.mismatch_log(comparison)
        row['diagnostic_consistent']=row['status']==row['spec_diagnostic']['status']
    except lab.LabError as exc:
        row.update(status=exc.status,stage=exc.stage,message=exc.message)
    row['localization']=fsm_ir.localize(diagnosis['status'],row['status'],row['ir_rtl']['status'])
    if row.get('diagnostic_consistent') is False: row['localization']='CHECKER_INCONSISTENCY'
    return row


def worker(run,job_id):
    plan=read_plan(run,True); job=next(j for j in plan['jobs'] if j['id']==job_id)
    folder=run/'jobs'/job_id
    if (folder/'call').exists() or (folder/'result.json').exists(): raise ValueError('Started jobs are never reissued')
    if batch.read(folder/'started.json')['reserved_calls']!=(1 if plan['config']['mode']=='codex' else 0): raise ValueError('No reservation')
    spec=next(s for s in plan['tasks'] if s['id']==job['task']); case=next(c for c in plan['cases'] if c['id']==job['case'])
    raw=(bank.ROOT/case['ir_file']).read_text(encoding='utf-8')
    args=SimpleNamespace(**dict(plan['config'],model=job['model']))
    row=dict(job_id=job_id,task=job['task'],case=job['case'],pair_id=job['pair_id'],arm=job['arm'],sample=job['sample'],
             requested_model=job['model'],mode=args.mode,case_kind=case['kind'],error_type=case['error_type'],
             ir_sha256=case['ir_sha256'],directory=str(folder.relative_to(run)).replace('\\','/'))
    call=folder/'call'; call.mkdir(); start=time.monotonic()
    try:
        text=prompt(spec,raw,job['arm']); lab.write_text(call/'prompt.txt',text)
        batch.atomic(call/'started.json',dict(utc=lab.utc(),model_call=args.mode=='codex'))
        if args.mode=='codex': output,meta=codex_adapter.generate_text(args,call,text)
        else: output=(bank.ROOT/spec['id']/'reference.sv').read_text(encoding='utf-8'); meta=dict(usage=None,codex_generation_success=False,label='OFFLINE_FIXTURE')
        lab.write_text(call/'response.txt',output)
        meta['response_sha256']=lab.digest((call/'response.txt').read_bytes()); batch.atomic(call/'completed.json',meta)
        row.update(judge(folder,spec,output,raw,batch.read(run/'environment.json')['tools'],args))
    except lab.LabError as exc:
        row.update(status=exc.status,stage=exc.stage,message=exc.message,localization='INCONCLUSIVE')
    except (ValueError,OSError,KeyError) as exc:
        row.update(status='ENV_ERROR',stage='worker',message=str(exc),localization='INCONCLUSIVE')
    row['elapsed_seconds']=round(time.monotonic()-start,3); batch.atomic(folder/'result.json',row)
    return 0


def execute(run,job,config):
    folder=run/'jobs'/job['id']; env=lab.clean_env()
    for name in ('APPDATA','LOCALAPPDATA','CODEX_HOME'):
        if name in os.environ: env[name]=os.environ[name]
    kwargs=dict(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP) if os.name=='nt' else dict(start_new_session=True)
    command=[sys.executable,str(Path(__file__).resolve()),'_worker','--run-dir',str(run),'--job-id',job['id']]
    reason='ENV_ERROR'; deadline=time.monotonic()+config['api_timeout']+3*(config['compile_timeout']+config['sim_timeout'])+90
    with (folder/'worker.log').open('wb') as log:
        process=subprocess.Popen(command,cwd=batch.ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,**kwargs)
        while process.poll() is None:
            if batch.STOP.is_set() or time.monotonic()>deadline:
                reason='INTERRUPTED' if batch.STOP.is_set() else 'TIMEOUT'; batch.stop_worker(process); break
            time.sleep(.1)
    if not (folder/'result.json').exists():
        terminal(run,job,config,reason,'Worker ended without a final result')
    return batch.read(folder/'result.json')


def terminal(run,job,config,status,message):
    folder=run/'jobs'/job['id']
    batch.atomic(folder/'result.json',dict(job_id=job['id'],task=job['task'],case=job['case'],pair_id=job['pair_id'],
        arm=job['arm'],sample=job['sample'],requested_model=job['model'],mode=config['mode'],status=status,
        localization='INCONCLUSIVE',message=message,directory=str(folder.relative_to(run)).replace('\\','/')))


def reserve(run,job,plan):
    folder=run/'jobs'/job['id']
    if folder.exists(): raise ValueError('Reservation cannot be reused')
    count=int(plan['config']['mode']=='codex')
    spent=sum(batch.read(p)['reserved_calls'] for p in (run/'jobs').glob('*/started.json'))
    if spent+count>plan['max_calls']: return False
    folder.mkdir(parents=True); batch.atomic(folder/'started.json',dict(utc=lab.utc(),reserved_calls=count)); return True


def run_jobs(run,workers=2,max_jobs=None):
    plan=read_plan(run,True); config=plan['config']
    if not 1<=workers<=2 or (max_jobs is not None and max_jobs<0): raise ValueError('Invalid concurrency/count')
    with batch.lock(run):
        tools=lab.inspect_tools(SimpleNamespace(**config),run); codex=None
        if config['mode']=='codex':
            exe=codex_adapter.find_codex(); codex=dict(path=exe,sha256=lab.digest(Path(exe).read_bytes()))
            # The per-call adapter also checks login and forbids tool use.
            env=lab.clean_env()
            for name in ('APPDATA','LOCALAPPDATA','CODEX_HOME'):
                if name in os.environ: env[name]=os.environ[name]
            auth=lab.run_process([exe,'login','status'],run,20,env)
            if auth['returncode'] or 'Logged in using ChatGPT' not in auth['stdout']+auth['stderr']: raise ValueError('ChatGPT login unavailable')
        environment=dict(tools=tools,codex=codex)
        if (run/'environment.json').exists() and batch.read(run/'environment.json')!=environment: raise ValueError('Environment changed')
        batch.atomic(run/'environment.json',environment)
        for job in plan['jobs']:
            folder=run/'jobs'/job['id']
            if folder.exists() and not (folder/'result.json').exists(): terminal(run,job,config,'INTERRUPTED','Unknown outcome; no refund or model retry')
        todo=[j for j in plan['jobs'] if batch.latest(run,j) is None]
        if max_jobs is not None: todo=todo[:max_jobs]
        batch.STOP.clear(); old={s:signal.signal(s,lambda *_:batch.STOP.set()) for s in (signal.SIGINT,signal.SIGTERM)}
        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                active={}; queue=iter(todo); exhausted=False
                while active or not exhausted:
                    while len(active)<workers and not exhausted and not batch.STOP.is_set():
                        job=next(queue,None)
                        if job is None or not reserve(run,job,plan): exhausted=True; break
                        active[pool.submit(execute,run,job,config)]=job
                    if batch.STOP.is_set(): exhausted=True
                    if not active: break
                    done,_=wait(active,timeout=.5,return_when=FIRST_COMPLETED)
                    for future in done:
                        job=active.pop(future); row=future.result(); summary=report(run)
                        print(f"[{summary['completed']}/{summary['planned']}] {job['id']}: {row['status']} / {row['localization']}",flush=True)
                        if row['status'] in ('API_ERROR','ENV_ERROR','INTERRUPTED','TIMEOUT') or row['localization']=='CHECKER_INCONSISTENCY': exhausted=True
        finally:
            for s,handler in old.items(): signal.signal(s,handler)
            summary=report(run)
    return int(bool(summary['pending'] or summary['infra_failures'] or summary['checker_inconsistencies']))


def report(run):
    plan=read_plan(run); rows=[batch.latest(run,j) for j in plan['jobs']]; rows=[r for r in rows if r]
    groups=[]
    for model in MODELS:
        for arm in ARMS:
            selected=[r for r in rows if r['requested_model']==model and r['arm']==arm]; usage=Counter()
            for row in selected:
                meta=run/'jobs'/row['job_id']/'call/completed.json'
                if meta.exists(): usage.update({k:v for k,v in (batch.read(meta).get('usage') or {}).items() if type(v) is int})
            groups.append(dict(model=model,arm=arm,planned=sum(j['model']==model and j['arm']==arm for j in plan['jobs']),
                completed=len(selected),passes=sum(r['status']=='PASS' for r in selected),counts=dict(Counter(r['status'] for r in selected)),
                localizations=dict(Counter(r['localization'] for r in selected)),usage=dict(usage)))
    pairs=[]
    for key in dict.fromkeys(j['pair_id'] for j in plan['jobs']):
        selected={r['arm']:r for r in rows if r['pair_id']==key}
        if len(selected)!=2: continue
        a,b=(selected[k]['status']=='PASS' for k in ARMS)
        pairs.append(dict(pair_id=key,case=selected['control']['case'],model=selected['control']['requested_model'],
                          control_pass=a,feedback_pass=b,outcome='both_pass' if a and b else 'feedback_only' if b else 'control_only' if a else 'both_fail'))
    metadata=[batch.read(p) for p in (run/'jobs').glob('*/call/completed.json')]
    summary=dict(schema=1,kind=plan['kind'],stage=plan['stage'],mode=plan['config']['mode'],planned=len(plan['jobs']),completed=len(rows),pending=len(plan['jobs'])-len(rows),
        max_calls=plan['max_calls'],model_call_reservations=sum(batch.read(p)['reserved_calls'] for p in (run/'jobs').glob('*/started.json')),
        model_turns_started=sum(batch.read(p)['model_call'] for p in (run/'jobs').glob('*/call/started.json')),
        real_generations=sum(bool(m.get('codex_generation_success')) for m in metadata),
        infra_failures=sum(r['status'] in ('API_ERROR','ENV_ERROR','INTERRUPTED','TIMEOUT') for r in rows),
        checker_inconsistencies=sum(r['localization']=='CHECKER_INCONSISTENCY' for r in rows),
        groups=groups,pair_counts=dict(Counter(p['outcome'] for p in pairs)),pairs=pairs,results=rows,
        limitations=['Conditional repair of fixed erroneous tables, not end-to-end generation accuracy.',
                    'Injected faults and one retained natural error must be reported separately.',
                    'Two repeats and a small number of families do not establish population efficacy.',
                    'Equal new-turn count; token use and cached input differ. No paired random seed is exposed.'])
    batch.atomic(run/'summary.json',summary)
    fields=['job_id','case','task','requested_model','arm','sample','status','localization','rtl_sha256']
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
    for job in plan['jobs']:
        row=next((r for r in rows if r['job_id']==job['id']),{})
        writer.writerow({k:row.get(k,job.get(k,'PENDING' if k=='status' else '')) for k in fields})
    (run/'summary.csv').write_bytes(stream.getvalue().encode('utf-8-sig'))
    table=''.join('<tr>'+''.join('<td>'+html.escape(str(g[k]))+'</td>' for k in ('model','arm','passes','completed','planned'))+'</tr>' for g in groups)
    lab.write_text(run/'report.html','<!doctype html><meta charset="utf-8"><title>Paired feedback</title><style>body{font:16px system-ui;margin:3em}td,th{padding:1em;border:1px solid #ccc}</style><h1>固定错误表：配对反馈实验 '+plan['stage']+'</h1><table><tr><th>模型</th><th>条件</th><th>通过</th><th>完成</th><th>计划</th></tr>'+table+'</table><p>'+html.escape(json.dumps(summary['pair_counts']))+'</p>')
    return summary


def curate(run,dest):
    summary=report(run); plan=read_plan(run)
    if summary['pending']: raise ValueError('Finish all planned samples before curation')
    if dest.exists(): raise ValueError('Evidence already exists')
    dest.mkdir(parents=True)
    for name in ('plan.json','plan-lock.json','summary.json','summary.csv','report.html','environment.json'):
        (dest/name).write_bytes((run/name).read_bytes())
    for job in plan['jobs']:
        source=run/'jobs'/job['id']; target=dest/'jobs'/job['id']; target.mkdir(parents=True)
        row=batch.read(source/'result.json')
        for name in ('result.json','started.json','dut.sv'):
            if (source/name).exists(): (target/name).write_bytes((source/name).read_bytes())
        if row.get('rtl_sha256') and lab.digest((target/'dut.sv').read_bytes())!=row['rtl_sha256']: raise ValueError('DUT changed')
        if (source/'call').exists():
            (target/'call').mkdir()
            for name in ('prompt.txt','response.txt','started.json'):
                if (source/'call'/name).exists(): (target/'call'/name).write_bytes((source/'call'/name).read_bytes())
            if (source/'call/completed.json').exists():
                meta=batch.read(source/'call/completed.json'); meta.pop('codex_thread_id',None)
                if lab.digest((target/'call/response.txt').read_bytes())!=meta['response_sha256']: raise ValueError('Response changed')
                batch.atomic(target/'call/completed.json',meta)
    for source,name in [('synthesis-review/summary.json','synthesis-summary.json'),('synthesis-review/environment.json','synthesis-environment.json')]:
        if (run/source).exists(): (dest/name).write_bytes((run/source).read_bytes())
    batch.atomic(dest/'evidence-lock.json',{str(p.relative_to(dest)).replace('\\','/'):lab.digest(p.read_bytes()) for p in dest.rglob('*') if p.is_file()})


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    for name in ('init','run','report','curate','_worker'):
        c=sub.add_parser(name); c.add_argument('--run-dir',required=True)
        if name=='init':
            c.add_argument('--stage',choices=('A','B'),required=True); c.add_argument('--mode',choices=('codex','offline'),default='codex')
            c.add_argument('--repeats',type=int,default=2); c.add_argument('--previous')
        elif name=='run': c.add_argument('--workers',type=int,default=2); c.add_argument('--max-jobs',type=int)
        elif name=='curate': c.add_argument('--destination',required=True)
        elif name=='_worker': c.add_argument('--job-id',required=True)
    args=p.parse_args(argv); run=Path(args.run_dir).resolve()
    try:
        if args.command=='init': init(run,args.stage,args.mode,args.repeats,Path(args.previous).resolve() if args.previous else None)
        elif args.command=='run': return run_jobs(run,args.workers,args.max_jobs)
        elif args.command=='report':
            r=report(run); print(json.dumps({k:v for k,v in r.items() if k not in ('results','pairs')},indent=2))
        elif args.command=='curate': curate(run,Path(args.destination).resolve())
        else: return worker(run,args.job_id)
    except (ValueError,OSError,KeyError,lab.LabError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr); return 2
    return 0


if __name__=='__main__': raise SystemExit(main())
