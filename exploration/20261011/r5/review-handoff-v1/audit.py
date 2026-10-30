"""Read frozen R5 evidence and local diagnostic logs; write only this new packet."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
R5 = OUT.parent
RUN = R5 / 'runs/prepared-v1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(name, data):
    p = OUT / name
    if p.exists():
        raise RuntimeError('New diagnostic output already exists: ' + str(p))
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def verify(lock, base):
    bindings = read(lock)
    failures = []
    for name, expected in bindings.items():
        p = Path(name) if Path(name).is_absolute() else base / name
        if not p.is_file() or sha(p) != expected:
            failures.append(name)
    return {'lock': str(lock), 'lock_sha256': sha(lock), 'bindings': len(bindings), 'failures': failures}

checks = [verify(R5/'results-packet-lock.json', R5),
          verify(RUN/'evidence-lock.json', RUN),
          verify(R5/'packet-lock.json', R5)]
seal = read(RUN/'evidence-lock.json')
actual = {str(p.relative_to(RUN)) for p in RUN.rglob('*') if p.is_file()
          and p.name not in ['evidence-lock.json', 'run.lock']}
assert actual == set(seal), 'Run seal file set differs'
assert all(not c['failures'] for c in checks), 'Frozen evidence changed'
plan = read(RUN/'plan.json')
known, unknown, pending, threads = [], [], [], []
usage = dict(input_tokens=0, output_tokens=0, cached_input_tokens=0,
             cache_write_input_tokens=0, reasoning_output_tokens=0)
for job in plan['jobs']:
    p = RUN/'jobs'/job['id']
    if not (p/'started.json').exists():
        assert not (p/'generation.json').exists()
        pending.append(job['id'])
        continue
    gen = read(p/'generation.json')
    if gen['status'] != 'GENERATED':
        assert gen['status'] == 'UNKNOWN_INTERRUPTED' and gen['usage'] is None
        assert not any((p/'call'/n).exists() for n in ['codex.json', 'codex.stdout.log', 'model_output.raw.txt'])
        unknown.append({'id': job['id'], 'started': read(p/'started.json'), 'generation': gen})
        continue
    proc = read(p/'call/codex.json')
    assert proc['returncode'] == 0 and not any(proc[k] for k in ['timeout', 'output_limit', 'killed'])
    events = [json.loads(s) for s in (p/'call/codex.stdout.log').read_text(encoding='utf-8').splitlines() if s.strip()]
    completed = [e for e in events if e.get('type') == 'turn.completed']
    assert len(completed) == 1
    assert not any(e.get('type') in ['error', 'turn.failed'] for e in events)
    assert all(e.get('item', {}).get('type') == 'agent_message' for e in events if e.get('type') == 'item.completed')
    assert completed[0]['usage']['input_tokens'] == gen['usage']['input_tokens']
    assert completed[0]['usage']['output_tokens'] == gen['usage']['output_tokens']
    assert completed[0]['usage']['cached_input_tokens'] == gen['usage']['cached_input_tokens']
    for k in usage:
        usage[k] += gen['usage'][k]
    threads.append(gen['codex_thread_id'])
    known.append(job['id'])
assert (len(known), len(unknown), len(pending), len(set(threads))) == (20, 1, 27, 20)
analysis = read(R5/'actual-analysis.json')
assert usage == analysis['known_completed_usage']
half = {k: v['known_half_shared_usage'] for k,v in analysis['ledger'].items()}
assert {k: sum(v[k] for v in half.values()) for k in usage} == usage
assert all(v['denominator'] == 6 for v in analysis['ledger'].values())
save('verification.json', {
    'checked_utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS',
    'hash_checks': checks, 'run_seal_exact_file_set': True,
    'known_complete': known, 'unknown_reserved': unknown, 'unstarted': pending,
    'unique_clean_cli_turns': len(set(threads)), 'known_usage': usage,
    'known_half_shared_usage': half, 'reserved_half_calls': {k:v['reserved_half'] for k,v in analysis['ledger'].items()},
    'total_provider_usage': 'UNKNOWN', 'money_cost': 'UNKNOWN',
    'reasoning_accounting': '744 is a subset of output 6156; do not add again',
    'policy': 'No model call, replay, simulator, score rewrite or old-file write; no price inference.'})

logdir = Path('C:/Users/A/AppData/Local/Codex/Logs/2026/10/11')
old = logdir/'codex-desktop-b378a793-93da-4617-9d18-7b075a227c89-21400-t0-i1-005311-1.log'
new = logdir/'codex-desktop-9e472348-8ef1-475c-89ac-175f12b10cfa-42584-t0-i1-072059-0.log'
selected = []
for source in [old, new]:
    for number, line in enumerate(source.read_text(encoding='utf-8').splitlines(), 1):
        keep = (source == old and '2026-10-11T06:12:30.' in line and
                any(s in line for s in ['EPIPE', 'Stopping app-server transport', 'cause=stop_process']))
        keep |= (source == new and any(s in line for s in ['Launching app', 'stdio_transport_spawned']) and '2026-10-11T07:2' in line)
        keep |= (source == new and 'hostId=local' in line and 'next=connected' in line and '2026-10-11T07:21:00.' in line)
        if keep:
            selected.append({'source': str(source), 'line_number': number,
                             'line_sha256': hashlib.sha256(line.encode()).hexdigest(),
                             'excerpt': line.split('errorStack=')[0][:750]})
assert any('cause=stop_process' in x['excerpt'] for x in selected)
assert any('Launching app' in x['excerpt'] for x in selected)
save('local-lifecycle-evidence.json', {
    'selected_lines': selected,
    'unknown_reservation_utc': unknown[0]['started']['utc'],
    'observed': 'Local app-server stopped at 06:12:30 UTC; a new desktop instance launched at 07:21 UTC.',
    'inference': 'Host lifecycle interruption closely follows reservation 21 and supports local infrastructure interruption.',
    'unresolved': 'Stop trigger (manual close/restart, update, crash or other) and exact child termination mechanism are not established.',
    '403_boundary': 'Existing durable websocket 403 records are a different channel; they do not establish an R5 CLI/provider 403. No retry was performed.',
    'capture_scope': 'Selected diagnostic lines only; line hashes, not immutable whole-file claims for active logs. No raw session or credential export.'})
print(json.dumps({'status':'PASS', 'bindings':[c['bindings'] for c in checks],
                  'known':20, 'unknown':1, 'pending':27, 'selected_log_lines':len(selected)}))
