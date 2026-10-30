"""Read-only source/input preservation audit; does not import executors."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = json.loads((HERE / 'baseline-hashes.json').read_text())
    changed = [p for p, h in baseline.items() if sha(ROOT / p) != h]
    executor = ROOT / 'exploration/20261024/public-rag-next-executor-v1'
    counts = {}
    failures = []
    for name in ('source-lock.json', 'input-lock.json'):
        lock = json.loads((executor / name).read_text())
        counts[name] = len(lock)
        for path, expected in lock.items():
            source = Path(path)
            if not source.is_absolute():
                source = executor / source
            if not source.is_file() or sha(source) != expected:
                failures.append(path)
    result = dict(baseline_count=len(baseline), baseline_changed=changed,
                  lock_counts=counts, mismatches=failures,
                  passed=not changed and not failures,
                  model_calls=0, eda_calls=0)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
