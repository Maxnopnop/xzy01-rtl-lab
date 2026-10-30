"""Python 3.6+ manual one-netlist fixed-test simulation on the school host.

No synthesis, retries, SSH, model calls, or exported library bytes.
The payload is prepared locally from reviewed, hash-bound school returns.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import zipfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def verdict(text, nonce, code):
    lines = text.strip().splitlines()
    pattern = r'RTL_LAB_V1 ' + re.escape(nonce) + r' checks=(\d+) errors=(\d+)'
    match = re.fullmatch(pattern, lines[0]) if len(lines) == 1 else None
    if not match:
        return 'INVALID_RECEIPT'
    if code != 0:
        return 'SIM_ERROR'
    if int(match.group(1)) != 1840:
        return 'INCOMPLETE_CHECKS'
    return 'FIXED_TEST_PASS' if int(match.group(2)) == 0 else 'FUNCTION_FAIL'


def choose_model(root, required):
    """Select one unmodified school model defining every mapped cell.

    Fail closed for split models; do not invent substitute logic or silently
    combine files with duplicate definitions. Search only this exact PDK.
    """
    start = time.monotonic()
    candidates = []
    inspected = 0
    dirs_seen = 0
    for folder, dirs, files in os.walk(str(root), followlinks=False):
        dirs.sort()
        dirs_seen += 1
        if dirs_seen > 500 or time.monotonic() - start > 30:
            raise ValueError('PDK search bound reached; no simulation started')
        for name in sorted(files):
            path = Path(folder) / name
            if path.suffix.lower() not in ('.v', '.sv'):
                continue
            inspected += 1
            if inspected > 500:
                raise ValueError('Too many Verilog candidates; no simulation started')
            if path.stat().st_size > 20 * 1024 * 1024:
                continue
            text = path.read_text(errors='replace')
            modules = set(re.findall(r'\bmodule\s+([A-Za-z_]\w*)\b', text))
            if required <= modules:
                candidates.append(path)
    if not candidates:
        raise ValueError('No single PDK Verilog model defines all required cells: ' + ','.join(sorted(required)))
    # Prefer ordinary functional models to a directory explicitly named timing.
    candidates.sort(key=lambda p: ('timing' in str(p).lower(), len(str(p)), str(p)))
    return candidates[0], candidates


def collect(work, destination):
    # Explicit allowlist. Library models, tool installation files, license
    # configuration, simulation binaries, and generated tool databases excluded.
    allowed = ['ece_gate_check.py', 'manifest.json', 'payload-lock.json', 'testbench.sv',
               'rt_sequence.hex', 'netlist.v', 'execution.json', 'result.json',
               'run.csh', 'run.tcl', 'tool_version.log', 'launcher.log',
               'xrun.log', 'verdict.txt', 'simulate.exit']
    name = 'return-' + work.name
    archive = work / (name + '.zip')
    with zipfile.ZipFile(str(archive), 'x', zipfile.ZIP_DEFLATED) as z:
        for item in allowed:
            path = work / item
            if path.is_file() and not path.is_symlink():
                if path.stat().st_size > 20 * 1024 * 1024:
                    raise ValueError('Log too large for automatic return: ' + item)
                z.write(str(path), item)
    sidecar = work / (name + '.json')
    save(sidecar, dict(kind='mapped_fixed_test', archive=archive.name,
                      archive_sha256=sha(archive), school_work=str(work)))
    try:
        destination.mkdir(parents=True, exist_ok=True)
        for src in (archive, sidecar):
            target = destination / src.name
            with target.open('xb') as stream:
                stream.write(src.read_bytes())
            if sha(src) != sha(target):
                raise ValueError('Transport hash mismatch')
        print('RETURN COPIED: ' + str(destination / archive.name), flush=True)
    except (OSError, ValueError) as exc:
        print('RETURN RETAINED: ' + str(archive) + ' (' + str(exc) + ')', flush=True)


def run(tool, source, destination):
    if os.name != 'posix':
        raise ValueError('Run only on school Linux; no local commercial tool launched')
    manifest = json.loads((source / 'manifest.json').read_text())
    lock = json.loads((source / 'payload-lock.json').read_text())
    for name, digest in lock.items():
        if Path(name).name != name or sha(source / name) != digest:
            raise ValueError('Payload hash mismatch: ' + name)
    selected = manifest['netlists'][tool]
    netlist = Path(selected['school_session']) / 'outputs' / 'netlist.v'
    if sha(netlist) != selected['netlist_sha256']:
        raise ValueError('School netlist differs from reviewed synthesis return')
    setup = Path('/usr/eelocal/cadence/xcelium2303hf/.cshrc')
    if not setup.is_file() or not shutil.which('tcsh'):
        raise ValueError('Missing previously verified Xcelium setup or tcsh')
    key = 'xzy01-gate-' + tool + '-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    work = Path.home() / 'xzy01-gate-checks' / key
    work.mkdir(parents=True)
    for name in ('ece_gate_check.py', 'manifest.json', 'payload-lock.json', 'testbench.sv', 'rt_sequence.hex'):
        shutil.copyfile(str(source / name), str(work / name))
    shutil.copyfile(str(netlist), str(work / 'netlist.v'))
    nonce = uuid.uuid4().hex
    record = dict(kind='mapped_fixed_test', tool=tool, host=os.uname().nodename,
                  nonce=nonce, checks_required=1840, source=selected,
                  original_rtl_sha256=manifest['original_rtl_sha256'],
                  testbench_sha256=sha(work / 'testbench.sv'),
                  vectors_sha256=sha(work / 'rt_sequence.hex'),
                  setup_sha256=sha(setup), status='PREFLIGHT', returncode=None,
                  mode='No SDF; specify timing disabled; fixed-test functionality only')
    save(work / 'execution.json', record)
    print('ONE MAPPED NETLIST: ' + tool, flush=True)
    print('WORK: ' + str(work), flush=True)
    try:
        required = set(re.findall(r'^\s*(\w+_X\d+)\s+', netlist.read_text(), re.M))
        if not required:
            raise ValueError('No mapped cell instances found')
        model, candidates = choose_model(Path(manifest['school_pdk_root']), required)
        record['library_model'] = dict(path=str(model), sha256=sha(model),
                                      bytes=model.stat().st_size,
                                      candidates=[str(v) for v in candidates])
        print('CELL MODEL: ' + str(model), flush=True)
        # Preserve the previously verified harness as first compilation unit.
        # Keep its #2 sampling delays; -nospecify disables cell specify blocks.
        args = ['xrun', '-64bit', '-sv', '-nospecify', '-top', 'tb',
                'testbench.sv', 'netlist.v', '-v', str(model),
                '+incdir+' + str(model.parent), '+nonce=' + nonce,
                '-input', 'run.tcl', '-l', 'xrun.log']
        if any(re.search(r'[\s\"\$`!]', a) for a in args):
            raise ValueError('Unsupported shell character in model path')
        record['command'] = args
        script = ('#!/bin/tcsh -f\nsource "' + str(setup) + '"\n'
                  'if ($status != 0) exit 90\nrehash\n'
                  'xrun -version >& tool_version.log\n'
                  'if ($status != 0) exit 91\n' + ' '.join(args) + '\n'
                  'set sim_rc = $status\necho $sim_rc > simulate.exit\nexit $sim_rc\n')
        (work / 'run.csh').write_text(script)
        (work / 'run.tcl').write_text('run\nexit\n')
        record['status'] = 'STARTED'
        save(work / 'execution.json', record)
        with (work / 'launcher.log').open('wb') as output:
            process = subprocess.Popen(['tcsh', '-f', str(work / 'run.csh')],
                                       cwd=str(work), stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                record['returncode'] = process.wait(timeout=180)
                record['status'] = 'EXITED'
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                record.update(status='TIMEOUT_OR_INTERRUPTED', returncode=process.returncode)
        receipt = (work / 'verdict.txt').read_text() if (work / 'verdict.txt').is_file() else ''
        status = verdict(receipt, nonce, record['returncode']) if record['status'] == 'EXITED' else record['status']
        result = dict(status=status, receipt=receipt.strip(), execution_status=record['status'],
                      returncode=record['returncode'], checks_required=1840,
                      netlist_sha256=sha(work / 'netlist.v'),
                      functional_scope='Fixed 1840 checks only; no formal equivalence or SDF timing',
                      timing_status='NOT_VERIFIED_BY_THIS_SIMULATION')
    except (OSError, ValueError) as exc:
        record.update(status='PREFLIGHT_OR_ENV_ERROR', error=str(exc))
        result = dict(status='PREFLIGHT_OR_ENV_ERROR', error=str(exc))
    save(work / 'execution.json', record)
    save(work / 'result.json', result)
    print(json.dumps(result, indent=2), flush=True)
    collect(work, destination)
    return 0 if result['status'] == 'FIXED_TEST_PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=['dc', 'genus'])
    parser.add_argument('--return-dir', required=True)
    opts = parser.parse_args()
    try:
        sys.exit(run(opts.tool, Path(__file__).resolve().parent, Path(opts.return_dir)))
    except (OSError, ValueError, KeyError) as exc:
        print('STOP: ' + str(exc), flush=True)
        sys.exit(2)
