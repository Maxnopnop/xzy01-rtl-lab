"""Local historical experiment catalog, package preparation and return ingestion."""
import argparse
import csv
import datetime
import html
import json
from pathlib import Path
import shutil
import uuid
import batch
import ece_desktop as desktop
import ece_transfer as transfer

ROOT = Path(__file__).resolve().parent
DEFAULT_STATE = ROOT / 'workflow'
DEFAULT_SHARED = Path.home() / 'Documents' / 'FYP' / 'ECE-Transfer'


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))


def saved(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def history(root=ROOT):
    entries = []
    runs = root / 'runs'
    for plan_path in sorted(runs.glob('**/plan.json')):
        run = plan_path.parent; plan = read(plan_path)
        if 'jobs' not in plan or 'tasks' not in plan: continue
        rows = []
        for job in plan['jobs']:
            result = run / 'jobs' / job['id'] / 'result.json'
            if not result.exists(): continue
            row = read(result); folder = run / row.get('directory', 'jobs/' + job['id'])
            rows.append(dict(job_id=job['id'], task=job['task'], status=row.get('status'),
                exportable=(folder / 'dut.sv').is_file() and bool(row.get('rtl_sha256'))))
        entries.append(dict(run=str(run.relative_to(root)), planned=len(plan['jobs']),
            completed=len(rows), pending=len(plan['jobs'])-len(rows),
            exportable=sum(r['exportable'] for r in rows), jobs=rows))
    return entries


def registry(state):
    path = state / 'registry.json'
    return read(path) if path.exists() else dict(schema=1, packages=[], imports=[])


def publish(shared, reg):
    entries = [{k: p[k] for k in ('package_id','archive','archive_sha256','backend','label','cases')}
               for p in reg['packages'] if Path(p['shared_dir']).resolve() == shared.resolve()]
    saved(shared / 'ece-workflow-catalog.json', dict(schema=1, packages=entries,
        policy='Select and run ONE case manually; no EDA batch or SSH.'))
    for name in ('ece_station.py','ece_menu.sh'):
        shutil.copyfile(ROOT / name, shared / name)


def prepare(run, jobs, backends, shared, state=DEFAULT_STATE):
    selected = [j for j in jobs.split(',') if j]
    tools = backends.split(',')
    if not selected or len(selected) != len(set(selected)) or not tools or set(tools)-{'vcs','xcelium'} or len(tools)!=len(set(tools)):
        raise ValueError('Provide unique exact job IDs and vcs/xcelium backend(s)')
    reg = registry(state); prepared = []
    for backend in tools:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        package_id = 'ece-' + run.name + '-' + backend + '-' + stamp + '-' + uuid.uuid4().hex[:8]
        output = state / 'packages' / package_id
        archive = transfer.pack(run, output, backend, ','.join(selected))
        transfer.stage(archive, shared)
        package = desktop.verify(output)
        record = dict(package_id=package_id, archive=archive.name, archive_sha256=desktop.digest(archive),
            backend=backend, label=run.name, run_dir=str(run), package_dir=str(output),
            shared_dir=str(shared), cases=[dict(job_id=m['job_id'],task=m['task'],
                original_status=m['original_status'],hashes=m['hashes']) for m in package['cases']])
        reg['packages'].append(record); prepared.append(record)
        # Save each prepared backend before attempting the next one.
        saved(state / 'registry.json', reg); publish(shared, reg)
    return prepared


def ingest(shared, state=DEFAULT_STATE):
    reg = registry(state); issues = []; new = 0
    for sidecar in sorted((shared / 'inbox').glob('return-*.json')):
        try:
            info = read(sidecar)
            if Path(info['archive']).name != info['archive']: raise ValueError('Invalid return filename')
            archive = sidecar.parent / info['archive']
            expected = desktop.digest(archive)
            if expected != info['archive_sha256']: raise ValueError('Return hash mismatch')
            if any(i['zip_sha256'] == expected for i in reg['imports']): continue
            matches = [p for p in reg['packages'] if p['package_id']==info['package_id'] and p['archive_sha256']==info['package_sha256']]
            if len(matches)!=1: raise ValueError('Unknown original package')
            original = matches[0]
            if info['case'] not in {m['job_id'] for m in original['cases']}: raise ValueError('Unknown case')
            destination = state / 'returns' / uuid.uuid4().hex
            code = transfer.receive(Path(original['package_dir']), archive, destination)
            report = read(destination / 'import-report.json')
            meta = desktop.case_meta(Path(original['package_dir']), info['case'])
            returned_meta = read(destination / info['case'] / 'case.json')
            if returned_meta != meta: raise ValueError('Returned case metadata differs from original')
            execution = read(destination / info['case'] / 'execution.json')
            if execution.get('case') != info['case'] or execution.get('backend') != original['backend']:
                raise ValueError('Execution metadata mismatch')
            rows = [r for r in report['results'] if r['job_id']==info['case']]
            reg['imports'].append(dict(package_id=original['package_id'],backend=original['backend'],
                run_dir=original['run_dir'],case=info['case'],attempt=info['attempt'],zip_sha256=expected,
                report=str(destination / 'import-report.json'),results=rows))
            saved(state / 'registry.json',reg); new += 1
        except (KeyError, ValueError, OSError) as exc:
            issues.append(dict(file=sidecar.name,error=str(exc)))
    saved(state / 'ingest-issues.json',issues)
    print('Imported new returns: ' + str(new) + '; invalid returns: ' + str(len(issues)))
    status(state)
    return 1 if issues else 0


def status(state=DEFAULT_STATE):
    reg = registry(state); rows = []
    for package in reg['packages']:
        for case in package['cases']:
            attempts = [i for i in reg['imports'] if i['package_id']==package['package_id'] and i['case']==case['job_id']]
            verdict = attempts[-1]['results'][0]['status'] if attempts else 'NOT_RUN'
            rows.append(dict(experiment=package['run_dir'],job_id=case['job_id'],task=case['task'],
                backend=package['backend'],local=case['original_status'],commercial=verdict,
                attempts=len(attempts),package_id=package['package_id']))
    calibrated = []
    for backend in ('vcs','xcelium'):
        path = ROOT / ('evidence/ece-' + backend + '-smoke-20261008/result.json')
        if path.exists():
            data = read(path); calibrated.append(dict(backend=backend,status=data['status'],checks=data['checks'],
                errors=data['errors'],job_id=data['job_id'],note='Historical same-source smoke; not a result for new packages'))
    report = dict(packages=len(reg['packages']),returns=len(reg['imports']),rows=rows,
        historical_smoke=calibrated,limitations='One-case commercial verification does not establish full equivalence. No new model calls.')
    saved(state / 'status.json',report)
    with (state / 'status.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['experiment','job_id','task','backend','local','commercial','attempts','package_id']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    table=''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in fields)+'</tr>' for r in rows)
    page='<!doctype html><meta charset="utf-8"><title>ECE results</title><style>body{font:15px system-ui;margin:2em}td,th{border:1px solid #ddd;padding:.6em}table{border-collapse:collapse}</style><h1>ECE package results</h1><p>Each row binds one original package. NOT_RUN is unverified; historical smoke does not fill new results.</p><table><tr>'+''.join('<th>'+k+'</th>' for k in fields)+'</tr>'+table+'</table><h2>Historical calibration</h2><pre>'+html.escape(json.dumps(calibrated,ensure_ascii=False,indent=2))+'</pre>'
    (state/'report.html').write_text(page,encoding='utf-8')
    print('Packages: '+str(len(reg['packages']))+'; returns: '+str(len(reg['imports']))+'; report: '+str(state/'report.html'))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir',default=str(DEFAULT_STATE))
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('history')
    a=sub.add_parser('prepare');a.add_argument('--run-dir',required=True);a.add_argument('--jobs',required=True)
    a.add_argument('--backends',default='vcs,xcelium');a.add_argument('--shared-dir',default=str(DEFAULT_SHARED))
    a=sub.add_parser('ingest');a.add_argument('--shared-dir',default=str(DEFAULT_SHARED))
    sub.add_parser('status')
    args=p.parse_args();state=Path(args.state_dir).resolve()
    try:
        if args.command=='history':
            entries=history();saved(state/'history.json',entries)
            for e in entries: print(e['run']+' | planned='+str(e['planned'])+' completed='+str(e['completed'])+' exportable='+str(e['exportable']))
        elif args.command=='prepare':prepare(Path(args.run_dir).resolve(),args.jobs,args.backends,Path(args.shared_dir).resolve(),state)
        elif args.command=='ingest':return ingest(Path(args.shared_dir).resolve(),state)
        else:status(state)
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR: '+str(exc));return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
