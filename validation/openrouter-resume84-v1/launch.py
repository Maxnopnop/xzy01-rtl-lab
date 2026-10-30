"""Explicit continuation of slots 84..240, without altering stopped evidence."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent / 'exploration' / '20261023' / 'direct-api-v1'
sys.path.insert(0, str(BASE))
import core
import dispatcher

PARENT = BASE / 'runtime' / 'live-run'
LIVE = HERE / 'runtime' / 'continuation'

def verify_parent(parent, manifest, slots):
    assert not (parent / 'exclusive.lock').exists(), 'Parent still running'
    actual = {p.relative_to(parent).as_posix() for p in parent.rglob('*') if p.is_file()}
    assert actual == set(manifest), 'Parent file inventory changed'
    assert all(core.sha(parent / k) == v for k, v in manifest.items()), 'Parent evidence changed'
    assert core.read(parent / 'STOP.json')['reason'] == 'SERVICE_ERROR'
    expected = {s['id'] + '.json' for s in slots[:83]}
    for directory in ['reservations', 'results']:
        assert {p.name for p in (parent / directory).glob('*.json')} == expected, 'Parent prefix incomplete'
    for s in slots[:83]:
        r = core.read(parent / 'results' / (s['id'] + '.json'))
        assert r['request_sha256'] == s['request_sha256']
        if s['ordinal'] == 83:
            assert r['status'] == 'SERVICE_ERROR' and r['http_status'] == 429
        else:
            assert r['complete_http_return'] is True, 'Unknown earlier outcome'
    return core.read(parent / 'identity.json')['start_epoch']

def seed(parent, target, slots, manifest):
    """Only receipt copies, explicitly inherited; never delete the original STOP."""
    verify_parent(parent, manifest, slots)
    if target.exists():
        assert (target / 'inheritance.json').exists(), 'Incomplete seed; manual review required'
    else:
        target.mkdir(parents=True)
        for name in ['identity.json', 'run-binding.json']:
            core.save_bytes(target / name, (parent / name).read_bytes())
        for directory in ['reservations', 'results']:
            for s in slots[:83]:
                name = s['id'] + '.json'
                core.save_bytes(target / directory / name, (parent / directory / name).read_bytes())
        core.save(target / 'inheritance.json', {
            'parent': str(parent), 'inherited_ordinals': list(range(1, 84)),
            'new_allowed_ordinals': list(range(84, 241)),
            'inherited_receipts_are_not_new_calls': True,
            'original_stop_sha256': core.sha(parent / 'STOP.json'),
            'start_epoch_preserved': core.read(parent / 'identity.json')['start_epoch'],
        })
    for directory in ['reservations', 'results']:
        for s in slots[:83]:
            name = s['id'] + '.json'
            assert (target / directory / name).read_bytes() == (parent / directory / name).read_bytes()
    assert (target / 'identity.json').read_bytes() == (parent / 'identity.json').read_bytes()

def gate():
    report = {'ready': False, 'network_requests': 0, 'errors': []}
    try:
        release = core.read(HERE / 'release.json')
        assert release['decision'] == 'TECHNICAL_RELEASE_REMAINING_157'
        assert release['new_allowed_ordinals'] == list(range(84, 241))
        assert release['launch_lock_sha256'] == core.sha(HERE / 'launch-lock.json')
        assert all(core.sha(HERE / k) == v for k, v in core.read(HERE / 'launch-lock.json').items())
        assert release['base_release_sha256'] == core.sha(BASE / 'runtime' / 'technical-release.json')
        report = dispatcher.preflight(HERE / 'route.json', BASE / 'runtime' / 'technical-release.json')
        assert report['ready'], 'Base preflight blocked'
        slots = dispatcher.prepare_slots(core.read(HERE / 'route.json'))
        start = verify_parent(PARENT, core.read(HERE / 'parent-evidence-lock.json'), slots)
        assert 0 <= time.time() - start < 12000, 'Original wall-time budget exhausted; no reset'
        assert not (LIVE / 'STOP.json').exists(), 'Continuation stopped; no retry permitted'
        if LIVE.exists():
            seed(PARENT, LIVE, slots, core.read(HERE / 'parent-evidence-lock.json'))
        report.update(ready=True, continuation_start=84, new_attempt_cap=157,
                      original_stop_preserved=True, original_deadline_epoch=start + 12000)
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        report['ready'] = False
        report.setdefault('errors', []).append(str(exc) if isinstance(exc, AssertionError) else type(exc).__name__)
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['preflight', 'run'])
    args = parser.parse_args()
    report = gate()
    if args.command == 'preflight' or not report['ready']:
        print(json.dumps(report)); return 0 if report['ready'] else 2
    slots = dispatcher.prepare_slots(core.read(HERE / 'route.json'))
    seed(PARENT, LIVE, slots, core.read(HERE / 'parent-evidence-lock.json'))
    dispatcher.bind_run(LIVE, HERE / 'route.json')
    def send(slot, folder, timeout):
        assert 84 <= slot['ordinal'] <= 240, 'No resend of inherited slots'
        return dispatcher.live_transport(slot, folder, timeout, HERE / 'route.json')
    result = dispatcher.execute(LIVE, slots, 'LIVE', send, gate=gate, permitted=list(range(84, 241)))
    result.update(inherited_attempts=83, newly_reserved=result['reserved'] - 83,
                  total_is_cumulative_not_additive=True)
    core.save(LIVE / ('summary-' + uuid.uuid4().hex + '.json'), result)
    print(json.dumps(result)); return 1 if result['stopped'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
