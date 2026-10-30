"""Independent read-only evidence audit. No runner imports, subprocess or network."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SHARE = Path('C:/Users/A/Documents/FYP')
STATE = ROOT / 'validation/console-openrouter-20261024-v1'
LIVE = ROOT / 'exploration/20261024/public-rag-next-executor-v1/runtime/live-run'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(p):
    return json.loads(p.read_bytes())

def main():
    records = read(HERE / 'records.json')
    collection = read(HERE / 'collection-20261024T091514432317Z.json')
    rows = []
    for tool, record in records.items():
        checks = {}
        key = record['key']
        side = read(SHARE / ('return-' + key + '.json'))
        archive = SHARE / ('return-' + key + '.zip')
        raw = archive.read_bytes()
        sha = digest(raw)
        checks['sidecar_binding'] = side == dict(key=key, archive_sha256=sha, manifest_sha256=record['manifest_sha256'])
        local = Path(record['local'])
        checks['original_package_files_unchanged'] = all(digest((local / n).read_bytes()) == h for n,h in record['files'].items())
        inbox = Path(record['shared']) / 'inbox' / key
        checks['inbox_archive_identical'] = (inbox / 'console-return.zip').read_bytes() == raw
        checks['inbox_sidecar_identical'] = read(inbox / 'console-return.json') == side
        imported = STATE / 'school-returned' / sha
        checks['imported_archive_identical'] = (imported / 'original-return.zip').read_bytes() == raw
        imp = read(imported / 'import.json')
        checks['import_receipt_binding'] = imp['verified'] is True and imp['archive_sha256'] == sha and imp['key'] == key and imp['manifest_sha256'] == record['manifest_sha256']
        checks['collection_matches_import'] = next(r for r in collection['results'] if r['tool'] == tool) == dict(tool=tool, **imp)
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            m = json.loads(z.read('console-manifest.json'))
            result = json.loads(z.read('console-result.json'))
            allowed = set(m['inputs']) | {'console-manifest.json','console-result.json','launcher.log','simulate.log','compile.log','tool_version.log','simulate.exit','execution.json','doctor.json','tool.log','tool_path.txt','receipt.txt','outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt','reports/check_design.rpt','reports/constraints.rpt'}
            checks['zip_crc_unique_safe_whitelist'] = z.testzip() is None and len(names) == len(set(names)) and all(i.filename in allowed and not stat.S_ISLNK(i.external_attr >> 16) for i in z.infolist())
            checks['manifest_unchanged'] = digest(z.read('console-manifest.json')) == record['manifest_sha256']
            checks['declared_inputs_unchanged'] = all(digest(z.read(n)) == h for n,h in m['inputs'].items())
            checks['all_imported_members_identical'] = all((imported / n).read_bytes() == z.read(n) for n in names)
            checks['result_binding_and_normal_exit'] = result['key'] == key and result['manifest_sha256'] == record['manifest_sha256'] and result['returncode'] == 0
            provenance = {}
            for name,h in m['provenance'].items():
                candidates = list((LIVE / 'results').glob('*.json')) if name == 'result.json' else [LIVE / 'jobs/025' / name]
                provenance[name] = any(digest(p.read_bytes()) == h for p in candidates)
            checks['historical_provenance_unchanged'] = all(provenance.values())
            detail = dict(status=result['status'], returncode=result['returncode'], version_log=z.read('tool_version.log').decode(errors='replace'))
            if tool in ('vcs','xcelium'):
                log = z.read('simulate.log').decode(errors='replace')
                counts = re.findall(r'Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples', log)
                mismatch, samples = map(int, counts[-1])
                checks['simulation_log_matches_result'] = len(counts) == 1 and mismatch == result['mismatches'] and samples == result['samples'] and m['expected_checks'] == result['expected_samples'] and result['status'] == 'CHECK_COUNT_DIFFERENT' and samples != m['expected_checks']
                checks['simulation_exit_file_zero'] = z.read('simulate.exit').strip() == b'0'
                detail.update(mismatches=mismatch, samples=samples, expected_samples=m['expected_checks'], strict_simulation_pass=(mismatch == 0 and samples == m['expected_checks']), finish_ps=re.findall(r'Simulation finished at (\d+) ps',log))
            else:
                job = json.loads(z.read('job.json'))
                execution = json.loads(z.read('execution.json'))
                doctor = json.loads(z.read('doctor.json'))
                lock = json.loads(z.read('payload-lock.json'))
                checks['payload_lock_unchanged'] = all(digest(z.read(n)) == h for n,h in lock.items())
                checks['nonce_execution_receipt'] = execution['nonce'] == job['nonce'] and execution['package_id'] == key and execution['tool'] == tool and execution['status'] == 'EXITED' and execution['returncode'] == 0 and z.read('receipt.txt').decode().strip() == 'XZY01_SYNTH_V1 '+job['nonce']+' COMPLETE'
                required = ['outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt','reports/check_design.rpt']
                checks['required_synthesis_outputs_present'] = all(n in names and len(z.read(n)) > 0 for n in required)
                checks['doctor_bindings'] = doctor['missing'] == [] and doctor['sdc_sha256'] == job['sdc_sha256'] and [x['path'] for x in doctor['libraries']] == job['profile']['libraries'] and all(x['readable'] for x in doctor['libraries'])
                detail.update(execution=execution, doctor=doctor, required_output_hashes={n:digest(z.read(n)) for n in required}, synthesis_flow_complete=all(checks.values()))
            rows.append(dict(tool=tool, archive_sha256=sha, members=len(names), original_package_file_count=len(record['files']), declared_input_count=len(m['inputs']), provenance=provenance, checks=checks, all_integrity_checks_pass=all(checks.values()), detail=detail))
    out = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), mode='READ_ONLY_AUDIT', model_calls=0, school_tool_calls=0, results=rows, all_four_integrity_and_import_checks_pass=all(r['all_integrity_checks_pass'] for r in rows), full_functional_acceptance=False, reason='VCS 212 and Xcelium 211 checks vs frozen expected 213; original verdicts preserved. No gate-level equivalence/signoff claim.')
    (HERE/'return-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=out['all_four_integrity_and_import_checks_pass'], tools=[dict(tool=r['tool'], members=r['members'], inputs=r['declared_input_count'], failed_checks=[k for k,v in r['checks'].items() if not v]) for r in rows]),indent=2))
    return 0 if out['all_four_integrity_and_import_checks_pass'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
