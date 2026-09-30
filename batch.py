"""Resumable, bounded local RTL experiments. Python standard library only."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import csv
import html
import io
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import rtl_lab as lab

ROOT = Path(__file__).resolve().parent
STOP = threading.Event()
CODE_FILES = ['batch.py','rtl_lab.py','backends.py','codex_adapter.py','api_worker.py']


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def atomic(path, value):
    temp = path.with_name(path.name + '.tmp')
    temp.parent.mkdir(parents=True, exist_ok=True)
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)


@contextmanager
def lock(folder):
    """OS advisory lock releases on crash; no stale lock-file recovery required."""
    path=folder/'run.lock'
    with path.open('a+b') as f:
        if f.tell()==0: f.write(b'0'); f.flush()
        f.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            raise ValueError('This run is already being modified by another process') from None
        try: yield
        finally:
            f.seek(0)
            if os.name=='nt': msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(f.fileno(),fcntl.LOCK_UN)


def manifest():
    specs=read(ROOT/'tasks/manifest.json')
    ids=[s['id'] for s in specs]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate task IDs')
    for s in specs:
        if not s['id'].replace('_','').isalnum(): raise ValueError('Invalid task ID')
        assets={s['id']+'_tb.sv':s['tb_sha256'],**s.get('assets',{})}
        for name, expected in assets.items():
            if Path(name).name!=name or lab.digest((ROOT/'tasks'/name).read_bytes())!=expected:
                raise ValueError('Task asset hash mismatch: '+name)
    return specs


def identity():
    return {name:lab.digest((ROOT/name).read_bytes()) for name in CODE_FILES+['tasks/manifest.json']}


def init(args):
    run=Path(args.run_dir).resolve()
    if (run/'plan.json').exists(): raise ValueError('Run exists; use run or a new --run-dir')
    if run.exists() and any(run.iterdir()): raise ValueError('Choose a new or empty run directory')
    specs=manifest()
    selected=args.tasks.split(',') if args.tasks!='all' else [s['id'] for s in specs]
    if len(selected)!=len(set(selected)) or set(selected)-{s['id'] for s in specs}: raise ValueError('Unknown or duplicate task ID')
    specs=[s for s in specs if s['id'] in selected]
    n=len(specs)*args.samples
    if n<1 or n>10000: raise ValueError('Plan must contain 1..10000 samples')
    if args.mode!='offline' and not args.model: raise ValueError('Set --model explicitly')
    config={k:getattr(args,k) for k in ('mode','model','base_url','api_key_env','allow_anonymous','codex_executable',
        'codex_reasoning','temperature','seed','max_output_tokens','token_field','api_timeout','compile_timeout','sim_timeout','iverilog','vvp')}
    config.update(rtl_dir=str(Path(args.rtl_dir).resolve()),label={'offline':'OFFLINE_FIXTURE','codex':'LIVE_CODEX_CHATGPT','live':'LIVE_API'}[args.mode],backend='icarus')
    if args.mode=='live': lab.validate_endpoint(args.base_url,args.allow_anonymous,os.environ.get(args.api_key_env,''))
    fixtures={}
    if args.mode=='offline':
        fixtures={s['id']:lab.digest((Path(config['rtl_dir'])/(s['id']+'.sv')).read_bytes()) for s in specs}
    run.mkdir(parents=True,exist_ok=True)
    jobs=[{'id':f'{s["id"]}__s{i:03d}','task':s['id'],'sample':i} for i in range(1,args.samples+1) for s in specs]
    atomic(run/'plan.json',dict(schema=2,created_utc=lab.utc(),config=config,tasks=specs,jobs=jobs,
        source_hashes=identity(),fixture_hashes=fixtures,max_calls=args.max_calls if args.max_calls is not None else n,
        note='Local custom task suite; not VerilogEval. Offline repeats are not model samples.'))
    report(run)
    print(f'Plan: {n} samples, mode={args.mode}; {run}')


def latest(run,job):
    path=run/'jobs'/job['id']/'result.json'
    return read(path) if path.exists() else None


def report(run):
    plan=read(run/'plan.json')
    rows=[]
    for job in plan['jobs']:
        row=latest(run,job)
        if row: rows.append(row)
    counts=dict(Counter(r['status'] for r in rows))
    attempts=list((run/'jobs').glob('*/attempt_*/started.json'))
    calls=sum(read(p).get('model_call_reserved',False) for p in attempts)
    by_task=[]
    for spec in plan['tasks']:
        group=[r for r in rows if r['task']==spec['id']]
        target=sum(j['task']==spec['id'] for j in plan['jobs'])
        by_task.append(dict(task=spec['id'],category=spec.get('category','unknown'),planned=target,
                            completed=len(group),passes=sum(r['status']=='PASS' for r in group),counts=dict(Counter(r['status'] for r in group))))
    tokens=Counter()
    # Include all attempts, including explicit retries, rather than only final results.
    for p in (run/'jobs').glob('*/attempt_*/001_*/result.json'):
        for key,value in (read(p).get('usage') or {}).items():
            if isinstance(value,int):tokens[key]+=value
    successes=sum(r['status']=='PASS' for r in rows)
    generated=sum(bool(r.get('codex_generation_success') or r.get('live_api_success')) for r in rows)
    summary=dict(schema=2,mode=plan['config']['mode'],requested_model=plan['config']['model'],backend='icarus',
        planned=len(plan['jobs']),completed=len(rows),pending=len(plan['jobs'])-len(rows),counts=counts,
        pass_fraction_of_planned=successes/len(plan['jobs']),real_generations=generated,
        model_call_reservations=calls,recorded_token_usage=dict(tokens),by_task=by_task,results=rows,
        note='Denominator includes planned samples; unfinished and infrastructure failures remain visible. No public benchmark or formal-equivalence claim.')
    atomic(run/'summary.json',summary)
    fields=['job_id','task','sample','mode','requested_model','status','stage','message','elapsed_seconds','attempt','directory','rtl_sha256','testbench_sha256']
    output=io.StringIO(newline=''); writer=csv.DictWriter(output,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    # BOM improves opening directly in Windows Excel.
    (run/'summary.csv').write_text(output.getvalue(),encoding='utf-8-sig')
    tr=''.join('<tr>'+''.join('<td>'+html.escape(str(r.get(k,'')))+'</td>' for k in ('task','category','planned','completed','passes'))+'</tr>' for r in by_task)
    failures=''.join('<li>'+html.escape(r['job_id']+': '+r['status']+' — '+r.get('message',''))+'</li>' for r in rows if r['status']!='PASS')
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>RTL 实验结果</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:36px auto;padding:0 20px;color:#142b3a;background:#f8fafb}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}.stats{{padding:18px;background:#e2eef4;border-radius:12px}}code{{word-break:break-all}}</style>
<h1>RTL 本机批量实验</h1><p>{html.escape(plan['config']['mode'])} / {html.escape(plan['config']['model'] or '人工离线样例')} / Icarus</p>
<p class="stats">计划 {len(plan['jobs'])} · 完成 {len(rows)} · 通过 {successes} · 待完成 {summary['pending']} · 已记录真实生成 {generated}</p>
<p>本地自建任务集。离线样例只验证工具链，不代表模型成绩。仿真通过仅覆盖固定测试范围。</p>
<table><thead><tr><th>任务</th><th>类型</th><th>计划</th><th>完成</th><th>通过</th></tr></thead><tbody>{tr}</tbody></table>
<h2>失败与异常</h2><ul>{failures or '<li>当前没有已记录的失败</li>'}</ul>
<p><a href="summary.csv">CSV</a> · <a href="summary.json">完整 JSON</a></p></html>'''
    (run/'report.html').write_text(page,encoding='utf-8')
    return summary


def worker(run,job_id,attempt_dir):
    plan=read(run/'plan.json'); job=next(j for j in plan['jobs'] if j['id']==job_id)
    spec=next(s for s in plan['tasks'] if s['id']==job['task'])
    args=SimpleNamespace(**plan['config']); secret=os.environ.get(args.api_key_env,'') if args.mode=='live' else ''
    tools=read(run/'environment.json')['tools']
    row=lab.evaluate(args,attempt_dir,spec,1,tools,secret)
    row.update(job_id=job_id,sample=job['sample'],attempt=attempt_dir.name,
               directory=str((attempt_dir/row['directory']).relative_to(run)).replace('\\','/'))
    atomic(attempt_dir/'result.json',row)
    return 0


def stop_worker(proc):
    if proc.poll() is not None:return
    if os.name!='nt':
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
            return
        except (ProcessLookupError,subprocess.TimeoutExpired):pass
    lab.kill_tree(proc)


def execute_job(run,job,attempt,config):
    env=lab.clean_env()
    for name in ('APPDATA','LOCALAPPDATA','CODEX_HOME'):
        if name in os.environ:env[name]=os.environ[name]
    if config['mode']=='live' and config['api_key_env'] in os.environ:
        env[config['api_key_env']]=os.environ[config['api_key_env']]
    kwargs={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    started=time.monotonic(); reason=None
    with (attempt/'worker.log').open('wb') as output:
        proc=subprocess.Popen([sys.executable,str(ROOT/'batch.py'),'_worker','--run-dir',str(run),
            '--job-id',job['id'],'--attempt-dir',str(attempt)],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=output,**kwargs)
        limit=config['api_timeout']+config['compile_timeout']+config['sim_timeout']+60
        while proc.poll() is None:
            if STOP.is_set() or time.monotonic()-started>limit:
                reason='INTERRUPTED' if STOP.is_set() else 'TIMEOUT'
                stop_worker(proc);break
            time.sleep(.1)
    path=attempt/'result.json'
    if path.exists():row=read(path)
    else:row=dict(job_id=job['id'],task=job['task'],sample=job['sample'],mode=config['mode'],requested_model=config['model'],
        status=reason or 'ENV_ERROR',stage='worker',message='Worker interrupted or exited without result; inspect worker.log',
        directory=str(attempt.relative_to(run)).replace('\\','/'),attempt=attempt.name,elapsed_seconds=round(time.monotonic()-started,3))
    atomic(run/'jobs'/job['id']/'result.json',row)
    return row


def run_jobs(args):
    run=Path(args.run_dir).resolve();plan=read(run/'plan.json')
    if identity()!=plan['source_hashes']:raise ValueError('Code or task manifest changed; start a new run to preserve comparability')
    manifest()
    config=plan['config']
    for task,expected in plan['fixture_hashes'].items():
        if lab.digest((Path(config['rtl_dir'])/(task+'.sv')).read_bytes())!=expected:raise ValueError('Offline fixture changed')
    with lock(run):
        tools=lab.inspect_tools(SimpleNamespace(**config),run)
        envpath=run/'environment.json'
        if envpath.exists() and read(envpath)['tools']!=tools:raise ValueError('Simulator changed; create a new run')
        if config['mode']=='live':lab.validate_endpoint(config['base_url'],config['allow_anonymous'],os.environ.get(config['api_key_env'],''))
        codex=None
        if config['mode']=='codex':
            from codex_adapter import find_codex
            exe=find_codex(config['codex_executable'])
            env=lab.clean_env()
            for name in ('APPDATA','LOCALAPPDATA','CODEX_HOME'):
                if name in os.environ:env[name]=os.environ[name]
            auth=lab.run_process([exe,'login','status'],run,20,env)
            if auth['returncode']!=0 or 'Logged in using ChatGPT' not in auth['stdout']+auth['stderr']:
                raise ValueError('Codex ChatGPT login required: run codex login locally')
            codex={'executable':exe,'sha256':lab.digest(Path(exe).read_bytes())}
            if envpath.exists() and read(envpath).get('codex')!=codex:raise ValueError('Codex executable changed; create a new run')
        if not envpath.exists():atomic(envpath,dict(tools=tools,codex=codex,python=sys.version,platform=platform.platform()))
        if args.max_calls is not None:
            if args.max_calls<0:raise ValueError('max-calls must be nonnegative')
            plan['max_calls']=args.max_calls;atomic(run/'plan.json',plan)
        retry=set(args.retry_status.split(',')) if args.retry_status else set()
        todo=[j for j in plan['jobs'] if (latest(run,j) is None or latest(run,j)['status']=='INTERRUPTED' or latest(run,j)['status'] in retry)]
        if args.max_jobs is not None:todo=todo[:args.max_jobs]
        reserved=sum(read(p).get('model_call_reserved',False) for p in (run/'jobs').glob('*/attempt_*/started.json'))
        STOP.clear()
        old={s:signal.signal(s,lambda *_:STOP.set()) for s in (signal.SIGINT,signal.SIGTERM)}
        try:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                active={}; queue=iter(todo); exhausted=False
                while active or not exhausted:
                    while len(active)<args.workers and not exhausted and not STOP.is_set():
                        try:job=next(queue)
                        except StopIteration:exhausted=True;break
                        if config['mode']!='offline' and reserved>=plan['max_calls']:
                            print('Model call cap reached; remaining jobs stay pending.',flush=True);exhausted=True;break
                        jobdir=run/'jobs'/job['id'];jobdir.mkdir(parents=True,exist_ok=True)
                        attempt=jobdir/f'attempt_{len(list(jobdir.glob("attempt_*")))+1:03d}'
                        attempt.mkdir()
                        atomic(attempt/'started.json',dict(started_utc=lab.utc(),model_call_reserved=config['mode']!='offline'))
                        if config['mode']!='offline':reserved+=1
                        active[pool.submit(execute_job,run,job,attempt,config)]=job
                    if STOP.is_set():exhausted=True
                    if not active:break
                    done,_=wait(active,timeout=.5,return_when=FIRST_COMPLETED)
                    for future in done:
                        job=active.pop(future)
                        row=future.result()
                        summary=report(run)
                        print(f"[{summary['completed']}/{summary['planned']}] {job['id']}: {row['status']}",flush=True)
        finally:
            for s,handler in old.items():signal.signal(s,handler)
            summary=report(run)
        print(json.dumps({k:summary[k] for k in ('planned','completed','counts','pending','real_generations','model_call_reservations')},ensure_ascii=False))
        print('Report: '+str(run/'report.html'))
        return 0 if summary['completed']==summary['planned'] and summary['counts']=={'PASS':summary['planned']} else 1


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    new=sub.add_parser('init')
    new.add_argument('--run-dir',required=True)
    new.add_argument('--mode',choices=['offline','codex','live'],default='offline')
    new.add_argument('--model',default=os.environ.get('LLM_MODEL',''))
    new.add_argument('--tasks',default='all');new.add_argument('--samples',type=int,default=1)
    new.add_argument('--rtl-dir',default=str(ROOT/'examples/correct'))
    new.add_argument('--max-calls',type=int,default=None)
    new.add_argument('--base-url',default=os.environ.get('LLM_BASE_URL',''))
    new.add_argument('--api-key-env',default='LLM_API_KEY');new.add_argument('--allow-anonymous',action='store_true')
    new.add_argument('--codex-executable');new.add_argument('--codex-reasoning',choices=['low','medium','high','xhigh','max','ultra'],default='low')
    new.add_argument('--temperature',type=float);new.add_argument('--seed',type=int)
    new.add_argument('--max-output-tokens',type=int,default=4096)
    new.add_argument('--token-field',choices=['max_tokens','max_completion_tokens'],default='max_tokens')
    for option,default in [('api',180),('compile',15),('sim',10)]:new.add_argument('--'+option+'-timeout',type=lab.positive,default=default)
    new.add_argument('--iverilog',default=os.environ.get('IVERILOG'));new.add_argument('--vvp',default=os.environ.get('VVP'))
    go=sub.add_parser('run');go.add_argument('--run-dir',required=True);go.add_argument('--workers',type=int,default=2)
    go.add_argument('--max-jobs',type=int);go.add_argument('--max-calls',type=int);go.add_argument('--retry-status',default='')
    rep=sub.add_parser('report');rep.add_argument('--run-dir',required=True)
    work=sub.add_parser('_worker');work.add_argument('--run-dir',required=True);work.add_argument('--job-id',required=True);work.add_argument('--attempt-dir',required=True)
    args=p.parse_args(argv)
    try:
        if args.command=='list':
            for s in manifest():print(f"{s['id']:18s} {s.get('category',''):14s} checks={s['checks']}")
        elif args.command=='init':
            if args.samples<1 or args.max_output_tokens<1 or (args.max_calls is not None and args.max_calls<0):raise ValueError('Invalid count')
            if args.temperature is not None and not 0<=args.temperature<=2:raise ValueError('temperature must be in [0,2]')
            init(args)
        elif args.command=='run':
            if not 1<=args.workers<=16 or (args.max_jobs is not None and args.max_jobs<0):raise ValueError('workers must be 1..16; max-jobs nonnegative')
            return run_jobs(args)
        elif args.command=='report':report(Path(args.run_dir).resolve())
        else:return worker(Path(args.run_dir).resolve(),args.job_id,Path(args.attempt_dir).resolve())
    except (ValueError,OSError,KeyError,lab.LabError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
