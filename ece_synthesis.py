"""Local one-case DC/Genus packaging and evidence import; no EDA execution here."""
import argparse
import csv
import datetime
import html
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import zipfile

import batch
import rtl_lab as lab
from ece_synth_common import TOOLS, INPUTS, ARTIFACTS, REQUIRED, read, save, sha, template, validate_profile, verify, extract, copy_once, tcl, launcher

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'workflow' / 'synthesis'
CONFIG = ROOT / 'config.local.synthesis.json'
SHARED = Path.home() / 'Documents' / 'FYP' / 'ECE-Synthesis'


def registry(state=STATE):
    return read(state / 'registry.json') if (state / 'registry.json').exists() else dict(packages=[], imports=[])


def candidates():
    result = []
    for plan_file in sorted((ROOT / 'runs').glob('**/plan.json')):
        plan = read(plan_file)
        if 'jobs' not in plan or 'tasks' not in plan: continue
        for job in plan['jobs']:
            row = batch.latest(plan_file.parent, job)
            if row and row.get('rtl_sha256'):
                result.append(dict(run_dir=str(plan_file.parent), job_id=job['id'], status=row['status']))
    return result


def profile(config, tool):
    data = read(config)
    result = dict(data['tools'][tool])
    missing = validate_profile(tool, result)
    path = Path(result['sdc_file']) if result['sdc_file'] else None
    if path and not path.is_file(): missing.append('local SDC file not found')
    return result, missing


def publish(shared, state=STATE):
    reg = registry(state)
    entries = [{k: row[k] for k in ('package_id', 'archive', 'archive_sha256', 'tool', 'job_id', 'readiness')}
               for row in reg['packages'] if Path(row['shared_dir']).resolve() == shared.resolve()]
    save(shared / 'synthesis-catalog.json', dict(schema=1, packages=entries))
    for name in ('ece_synth_school.py', 'ece_synth_common.py', 'ece_synth_menu.sh'):
        shutil.copyfile(ROOT / name, shared / name)


def pack(run, job_id, tool, config=CONFIG, shared=SHARED, state=STATE):
    plan = read(run / 'plan.json')
    selected = [job for job in plan['jobs'] if job['id'] == job_id]
    if len(selected) != 1: raise ValueError('Select ONE exact existing job ID')
    job = selected[0]
    result = batch.latest(run, job)
    if not result or not result.get('rtl_sha256'): raise ValueError('Selected job has no accepted RTL')
    original = (run / result['directory'] / 'dut.sv').resolve()
    if not original.is_relative_to(run.resolve()) or sha(original) != result['rtl_sha256']:
        raise ValueError('Original RTL path/hash mismatch')
    spec = next(t for t in plan['tasks'] if t['id'] == job['task'])
    lab.extract_rtl(original.read_text(encoding='utf-8'), spec['module'])
    settings, missing = profile(config, tool)
    sdc = Path(settings['sdc_file']).read_bytes() if settings['sdc_file'] and Path(settings['sdc_file']).is_file() else b''
    sdc.decode('utf-8')
    if len(sdc) > 1024 * 1024: raise ValueError('SDC exceeds 1 MiB')
    if not sdc.strip(): missing.append('nonempty SDC')
    key = 'synth-' + tool + '-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    folder = state / 'packages' / key
    folder.mkdir(parents=True)
    shutil.copyfile(original, folder / 'dut.sv')
    (folder / 'constraints.sdc').write_bytes(sdc)
    # Keep local path out of the portable job; use only frozen package content.
    settings['sdc_file'] = 'constraints.sdc' if sdc else ''
    meta = dict(schema=1, package_id=key, tool=tool, top=spec['module'], job_id=job_id,
        source_result_sha256=sha(run / 'jobs' / job_id / 'result.json'), source_plan_sha256=sha(run / 'plan.json'),
        rtl_sha256=sha(original), sdc_sha256=sha(folder / 'constraints.sdc'), original_simulation=result['status'],
        nonce=uuid.uuid4().hex, profile=settings, expected_tool=TOOLS[tool],
        note='Completion requires report review; not functional equivalence, timing closure or signoff.')
    save(folder / 'job.json', meta)
    (folder / 'synthesis.tcl').write_text(tcl(tool, spec['module'], settings, meta['nonce']), encoding='utf-8', newline='\n')
    (folder / 'launch.csh').write_text(launcher(tool), encoding='utf-8', newline='\n')
    for name in ('ece_synth_common.py', 'ece_synth_school.py'):
        shutil.copyfile(ROOT / name, folder / name)
    save(folder / 'payload-lock.json', {name: sha(folder / name) for name in sorted(INPUTS)})
    archive = folder.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as zipped:
        for name in sorted(INPUTS | {'payload-lock.json'}): zipped.write(folder / name, name)
    copy_once(archive, shared / archive.name)
    row = dict(package_id=key, archive=archive.name, archive_sha256=sha(archive), tool=tool, job_id=job_id,
        package_dir=str(folder.resolve()), run_dir=str(run.resolve()), shared_dir=str(shared.resolve()),
        readiness='BLOCKED_PREREQUISITES' if missing else 'READY_FOR_SCHOOL_PREFLIGHT', missing=missing,
        corner=settings['corner'], rtl_sha256=meta['rtl_sha256'], source_result_sha256=meta['source_result_sha256'])
    reg = registry(state)
    reg['packages'].append(row)
    save(state / 'registry.json', reg)
    publish(shared, state)
    report(state)
    print('One-case package: ' + str(shared / archive.name))
    print('Readiness: ' + row['readiness'] + ('; missing: ' + ', '.join(missing) if missing else ''))
    return row


def judge(folder, original):
    if sha(folder / 'payload-lock.json') != sha(original / 'payload-lock.json'):
        raise ValueError('Returned input lock differs from original')
    job = verify(folder)
    execution = read(folder / 'execution.json')
    if any(execution.get(k) != job[k] for k in ('package_id', 'nonce', 'tool')):
        raise ValueError('Execution does not bind the selected synthesis job')
    doctor = read(folder / 'doctor.json')
    if doctor.get('tool') != job['tool'] or doctor.get('sdc_sha256') != job['sdc_sha256']:
        raise ValueError('Invalid school preflight binding')
    if execution['status'] == 'BLOCKED_PREREQUISITES':
        if not doctor.get('missing'): raise ValueError('Blocked result lacks prerequisite evidence')
        return 'BLOCKED_PREREQUISITES'
    if execution['status'] in ('TIMEOUT', 'INTERRUPTED', 'STARTED', 'ENV_ERROR'):
        return execution['status']
    if execution['status'] != 'EXITED': raise ValueError('Invalid execution status')
    if execution.get('returncode') != 0: return 'TOOL_FAILED'
    if doctor.get('missing') or validate_profile(job['tool'], job['profile']):
        raise ValueError('Success-shaped result has missing prerequisites')
    libraries = doctor.get('libraries', [])
    if [v.get('path') for v in libraries] != job['profile']['libraries'] or not all(v.get('readable') and isinstance(v.get('sha256'), str) and len(v['sha256']) == 64 for v in libraries):
        raise ValueError('Missing library fingerprint evidence')
    needed = REQUIRED + ('tool.log', 'tool_version.log', 'receipt.txt')
    if not all((folder / name).is_file() and (folder / name).stat().st_size for name in needed):
        return 'OUTPUT_INCOMPLETE'
    if (folder / 'receipt.txt').read_text().strip() != 'XZY01_SYNTH_V1 ' + job['nonce'] + ' COMPLETE':
        raise ValueError('Invalid synthesis completion receipt')
    # Do not promote zero exit + artifacts into functional or timing correctness.
    return 'COMPLETED_REVIEW_REQUIRED'


def ingest(shared=SHARED, state=STATE):
    reg = registry(state)
    issues = []
    imported = 0
    for sidecar in sorted((shared / 'inbox').glob('return-synth-*.json')):
        try:
            info = read(sidecar)
            if info.get('kind') != 'synthesis' or Path(info['archive']).name != info['archive']:
                raise ValueError('Invalid synthesis return metadata')
            source = sidecar.parent / info['archive']
            digest = sha(source)
            if digest != info['archive_sha256']: raise ValueError('Return ZIP hash mismatch')
            matches = [p for p in reg['packages'] if p['package_id'] == info['package_id']]
            if len(matches) != 1: raise ValueError('Unknown synthesis package')
            package = matches[0]
            original = Path(package['package_dir'])
            verify(original)
            if info['input_lock_sha256'] != sha(original / 'payload-lock.json'):
                raise ValueError('Input binding mismatch')
            if any(r['archive_sha256'] == digest for r in reg['imports']): continue
            target = state / 'returned' / digest
            if not target.exists():
                extract(source, target, INPUTS | ARTIFACTS | {'payload-lock.json'})
            else:
                with zipfile.ZipFile(source) as archive:
                    for name in archive.namelist():
                        if name not in INPUTS | ARTIFACTS | {'payload-lock.json'}:
                            raise ValueError('Unexpected existing return member')
                        if sha(target / name) != hashlib.sha256(archive.read(name)).hexdigest():
                            raise ValueError('Previously extracted return changed')
            status = judge(target, original)
            row = dict(package_id=package['package_id'], archive_sha256=digest, status=status,
                directory=str(target.resolve()), evidence_hashes={p.relative_to(target).as_posix(): sha(p) for p in target.rglob('*') if p.is_file()})
            reg['imports'].append(row)
            save(state / 'registry.json', reg)
            imported += 1
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
            issues.append(dict(file=sidecar.name, error=str(exc)))
    save(state / 'import-issues.json', issues)
    report(state)
    print('Synthesis returns imported: %d; invalid: %d' % (imported, len(issues)))
    return 1 if issues else 0


def report(state=STATE):
    reg = registry(state)
    rows = []
    for package in reg['packages']:
        returns = [r for r in reg['imports'] if r['package_id'] == package['package_id']]
        row = {k: package[k] for k in ('package_id', 'run_dir', 'job_id', 'tool', 'corner', 'rtl_sha256', 'source_result_sha256')}
        row.update(status=returns[-1]['status'] if returns else package['readiness'], attempts=len(returns),
            directory=returns[-1]['directory'] if returns else package['package_dir'])
        rows.append(row)
    save(state / 'summary.json', dict(rows=rows, note='School synthesis is separate from Yosys; completion requires manual report review.'))
    columns = ['package_id', 'job_id', 'tool', 'corner', 'status', 'attempts', 'directory']
    with (state / 'summary.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(r[k])) + '</td>' for k in columns[:-1]) +
        '<td><a href="' + html.escape(Path(r['directory']).as_uri(), quote=True) + '">查看文件</a></td></tr>' for r in rows)
    (state / 'report.html').write_text('<!doctype html><meta charset="utf-8"><title>DC / Genus</title><style>body{font:15px system-ui;padding:24px}td,th{border:1px solid #ccc;padding:8px}table{border-collapse:collapse}</style>'
        '<h1>学校综合：Design Compiler / Genus</h1><p>启动验证 ≠ 综合通过。COMPLETED_REVIEW_REQUIRED 表示输出已回收，需审阅库、约束、未解析引用和时序；不代表功能等价或时序达标。</p>'
        '<table><tr>' + ''.join('<th>' + k + '</th>' for k in columns) + '</tr>' + body + '</table>', encoding='utf-8')
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', default=str(STATE))
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('template', 'check'):
        child = sub.add_parser(name)
        child.add_argument('--config', default=str(CONFIG))
    sub.add_parser('list')
    child = sub.add_parser('pack')
    child.add_argument('--run-dir', required=True)
    child.add_argument('--job', required=True)
    child.add_argument('--tool', choices=TOOLS, required=True)
    child.add_argument('--config', default=str(CONFIG))
    child.add_argument('--shared-dir', default=str(SHARED))
    child = sub.add_parser('collect')
    child.add_argument('--shared-dir', default=str(SHARED))
    sub.add_parser('report')
    args = parser.parse_args(argv)
    state = Path(args.state_dir).resolve()
    try:
        if args.command == 'template':
            path = Path(args.config)
            if path.exists(): raise ValueError('Config already exists; edit it instead of overwriting')
            save(path, template())
        elif args.command == 'check':
            for tool in TOOLS:
                settings, missing = profile(Path(args.config), tool)
                print(tool + ': ' + ('BLOCKED: ' + ', '.join(missing) if missing else 'Configured; school library access/license not yet checked'))
        elif args.command == 'list': print(json.dumps(candidates(), indent=2))
        elif args.command == 'pack':
            pack(Path(args.run_dir).resolve(), args.job, args.tool, Path(args.config), Path(args.shared_dir).resolve(), state)
        elif args.command == 'collect': return ingest(Path(args.shared_dir).resolve(), state)
        else: report(state)
    except (ValueError, KeyError, OSError, lab.LabError) as exc:
        print('ERROR: ' + str(exc))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
