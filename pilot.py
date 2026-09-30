"""Frozen, resumable multi-model development pilot; no feedback or repair calls."""
import argparse
from collections import Counter
import csv
import html
import io
from pathlib import Path
import random
import statistics
import subprocess
import sys

import batch
import rtl_lab as lab


def init(root, config_path):
    config=batch.read(config_path)
    models=config['models'];specs=batch.manifest(config['suite'])
    if len(models) not in (2,4) or len(set(models))!=len(models):raise ValueError('Use 2 or 4 distinct models')
    if config['samples_per_task']!=3 or len(specs)!=10 or config['repair_budget']!=0:
        raise ValueError('This pilot requires 10 tasks, 3 samples and no repairs')
    if root.exists() and any(root.iterdir()):raise ValueError('Use a new pilot directory')
    root.mkdir(parents=True,exist_ok=True)
    runs=[]
    for i,model in enumerate(models):
        name=f'model_{i+1:02d}'
        args=['init','--run-dir',str(root/name),'--suite',config['suite'],'--mode',config['mode'],
              '--model',model,'--samples','3','--max-calls','30','--codex-reasoning',config['reasoning_effort'],
              '--api-timeout',str(config['api_timeout'])]
        if batch.main(args):raise ValueError('Failed to initialize model run')
        runs.append(dict(model=model,directory=name))
    batch.atomic(root/'pilot.json',dict(config=config,runs=runs,planned=30*len(models),
        pilot_source_sha256=lab.digest(Path(__file__).read_bytes()),
        note='Generation in Windows; synthesis review in WSL. Both consume exactly the same saved RTL bytes.'))
    report(root)


def run(root, max_blocks=None):
    plan=batch.read(root/'pilot.json');cfg=plan['config']
    if plan['pilot_source_sha256']!=lab.digest(Path(__file__).read_bytes()):raise ValueError('Pilot code changed; create a new pilot')
    blocks=0
    # Alternate model order by sample block. Resume skips already finished slots.
    for sample in range(1,4):
        runs=plan['runs'] if sample%2 else list(reversed(plan['runs']))
        for item in runs:
            folder=root/item['directory'];bp=batch.read(folder/'plan.json')
            block=[j for j in bp['jobs'] if j['sample']==sample]
            if all(batch.latest(folder,j) is not None for j in block):continue
            if max_blocks is not None and blocks>=max_blocks:return report(root)
            need=sum(batch.latest(folder,j) is None for j in block)
            result=subprocess.run([sys.executable,str(batch.ROOT/'batch.py'),'run','--run-dir',str(folder),
                 '--workers',str(cfg['workers']),'--max-jobs',str(need)],check=False)
            blocks+=1
            summary=report(root)
            latest=[batch.latest(folder,j) for j in block]
            if result.returncode not in (0,1) or any(r is None or r['status'] in ('API_ERROR','ENV_ERROR','INTERRUPTED') for r in latest):
                raise ValueError('Infrastructure failure: pilot stopped, evidence retained; do not replace a failed slot silently')
    return report(root)


def percentile(values,p):
    values=sorted(values);pos=(len(values)-1)*p;i=int(pos);f=pos-i
    return values[i]*(1-f)+values[min(i+1,len(values)-1)]*f


def bootstrap(task_values, specs, replicates=5000, seed=20260930):
    """Resample whole tasks (all three repeats together), stratified by benchmark.
    Shared resamples across models retain task pairing for differences.
    """
    groups={b:[s['id'] for s in specs if s['benchmark']==b] for b in sorted({s['benchmark'] for s in specs})}
    rng=random.Random(seed);draws=[[] for _ in task_values];diff=[]
    for _ in range(replicates):
        selected=[rng.choice(g) for g in groups.values() for _ in g]
        means=[statistics.mean(values[t] for t in selected) for values in task_values]
        for target,value in zip(draws,means):target.append(value)
        diff.append(means[1]-means[0])
    ci=lambda values:[percentile(values,.025),percentile(values,.975)]
    return dict(method='paired task-cluster percentile bootstrap, stratified by benchmark',
        seed=seed,replicates=replicates,confidence=.95,
        model_intervals=[ci(v) for v in draws],model_2_minus_model_1_interval=ci(diff),
        caveat='Only 10 development tasks. Degenerate intervals at all-pass are not evidence of perfect generalization.')


def report(root):
    plan=batch.read(root/'pilot.json');rows=[];models=[];first=None;specs=None
    for item in plan['runs']:
        folder=root/item['directory'];bp=batch.read(folder/'plan.json')
        if first is None:first=bp;specs=bp['tasks']
        elif bp['tasks']!=specs or bp['source_hashes']!=first['source_hashes']:
            raise ValueError('Model runs do not share frozen tasks/code')
        compared=('mode','codex_reasoning','api_timeout','compile_timeout','sim_timeout','temperature','seed','max_output_tokens')
        if any(bp['config'][k]!=first['config'][k] for k in compared):raise ValueError('Unmatched model settings')
        results=[]
        for job in bp['jobs']:
            sim=batch.latest(folder,job);synth='PENDING'
            if sim:
                if sim.get('rtl_sha256'):
                    rtl=(folder/sim['directory']/'dut.sv').resolve()
                    if not rtl.is_relative_to(folder) or lab.digest(rtl.read_bytes())!=sim['rtl_sha256']:
                        raise ValueError('Generated RTL changed after evaluation')
                synth=sim.get('synthesis_status','NOT_REQUESTED')
                extra=folder/'synthesis-review'/job['id']/'result.json'
                if extra.exists():
                    review=batch.read(extra)
                    if review['source_result_sha256']!=lab.digest((folder/'jobs'/job['id']/'result.json').read_bytes()) or review['rtl_sha256']!=sim.get('rtl_sha256'):
                        raise ValueError('Synthesis evidence does not match simulation')
                    synth=review['status']
                elif synth=='NOT_REQUESTED':synth='PENDING'
            status=sim['status'] if sim else 'PENDING'
            entry=dict(model=item['model'],task=job['task'],sample=job['sample'],status=status,
                       synthesis_status=synth,joint_pass=status=='PASS' and synth=='SYNTH_PASS',
                       generation_seconds=sim.get('generation_seconds') if sim else None,
                       rtl_sha256=sim.get('rtl_sha256') if sim else None)
            results.append(entry);rows.append(entry)
        summary=batch.report(folder)
        models.append(dict(model=item['model'],planned=len(results),completed=summary['completed'],
                           model_call_reservations=summary['model_call_reservations'],real_generations=summary['real_generations'],
                           simulation_passes=sum(r['status']=='PASS' for r in results),
                           synthesis_passes=sum(r['synthesis_status']=='SYNTH_PASS' for r in results),
                           joint_passes=sum(r['joint_pass'] for r in results),counts=dict(Counter(r['status'] for r in results)),
                           synthesis_counts=dict(Counter(r['synthesis_status'] for r in results)),
                           recorded_token_usage=summary['recorded_token_usage']))
    complete=all(r['status']!='PENDING' for r in rows)
    synth_complete=all(r['synthesis_status'] not in ('PENDING','NOT_REQUESTED') for r in rows)
    stats={}
    for metric,ready in [('simulation',complete),('joint',complete and synth_complete)]:
        if ready:
            values=[{s['id']:statistics.mean(float(r['status']=='PASS' if metric=='simulation' else r['joint_pass'])
                     for r in rows if r['model']==m['model'] and r['task']==s['id']) for s in specs} for m in models]
            stats[metric]=dict(estimates=[statistics.mean(v.values()) for v in values],
                **bootstrap(values,specs,plan['config']['bootstrap_replicates'],plan['config']['bootstrap_seed']))
    output=dict(schema=1,kind='DEVELOPMENT_PILOT_NOT_FINAL_BENCHMARK',planned=plan['planned'],
                completed=sum(m['completed'] for m in models),generation_complete=complete,synthesis_complete=synth_complete,
                models=models,statistics=stats,results=rows,
                note='All planned slots stay in denominator; failures and missing results are not removed. No pass@k or final benchmark claim.')
    batch.atomic(root/'pilot-summary.json',output)
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (root/'pilot-summary.csv').write_bytes(stream.getvalue().encode('utf-8-sig'))
    body=''.join('<tr>'+''.join('<td>'+html.escape(str(m[k]))+'</td>' for k in ('model','planned','completed','simulation_passes','synthesis_passes','joint_passes'))+'</tr>' for m in models)
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Dev10 pilot</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px}}th,td{{padding:12px;border-bottom:1px solid #ddd;text-align:left}}table{{border-collapse:collapse}}pre{{white-space:pre-wrap}}</style>
<h1>10 题开发集 · 多模型 pilot</h1><p>完成 {output['completed']} / {output['planned']} 次生成槽位。综合已全部评估：{synth_complete}。</p>
<table><tr><th>模型</th><th>计划</th><th>完成</th><th>仿真通过</th><th>综合通过</th><th>联合通过</th></tr>{body}</table>
<p>固定 5+5 开发题，每题 3 次。没有测试反馈或修复调用。综合失败与功能失败分开记录。</p>
<p>本结果来自适配开发子集，不是官方 benchmark 成绩或最终泛化结论。全部通过时 bootstrap 区间退化，不能据此宣称完美正确率。</p>
<p><a href="pilot-summary.json">完整结果和成对置信区间</a> · <a href="pilot-summary.csv">逐样本 CSV</a></p></html>'''
    (root/'pilot-report.html').write_text(page,encoding='utf-8')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['init','run','synthesize','report']);parser.add_argument('--run-dir',required=True)
    parser.add_argument('--config',default=str(batch.ROOT/'experiments/pilot60.json'));parser.add_argument('--max-blocks',type=int)
    args=parser.parse_args();root=Path(args.run_dir).resolve()
    try:
        if args.command=='init':init(root,Path(args.config))
        elif args.command=='run':
            with batch.lock(root):run(root,args.max_blocks)
        elif args.command=='synthesize':
            from synthesis import review
            with batch.lock(root):
                for item in batch.read(root/'pilot.json')['runs']:review(root/item['directory'])
                report(root)
        else:report(root)
    except (ValueError,OSError,KeyError,lab.LabError) as exc:parser.exit(2,'ERROR: '+str(exc)+'\n')


if __name__=='__main__':main()
