"""Prepare a bounded copy of the previously reviewed local-only CLI probe."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT/'exploration/20261023/cli-cache-repair-v1'
source = OLD/'offline_audit_candidate2.py'
text = source.read_text(encoding='utf-8')
replacements = {
    'B=R.parents[2]': 'B=R.parents[1]',
    "MODELS=['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol']": "MODELS=['gpt-5.6-luna']  # one local-only entry check; not a three-model certification",
    "for mode in ['401','403','429','disconnect','sse_disconnect']:": 'for mode in []:  # no extra launches in this bounded recheck',
    "'candidate_probe_cap':3,'retry_test_extra_cap':5": "'candidate_probe_cap':1,'retry_test_extra_cap':0",
    "'retry_modes':['400 (reuse initial Luna)','401','403','429','disconnect','sse_disconnect']": "'retry_modes':['400 entry check only; zero-retry production test NOT_EXECUTED']",
}
for old, new in replacements.items():
    assert text.count(old) == 1, old
    text = text.replace(old, new)
ast.parse(text)
for name, data in [('probe.py', text.encode()), ('bundled-catalog.json', (OLD/'bundled-catalog.json').read_bytes())]:
    with (HERE/name).open('xb') as stream:
        stream.write(data)
receipt = {'original_probe_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
           'new_probe_sha256': hashlib.sha256((HERE/'probe.py').read_bytes()).hexdigest(),
           'catalog_unchanged': (HERE/'bundled-catalog.json').read_bytes() == (OLD/'bundled-catalog.json').read_bytes(),
           'changes': replacements, 'model_generation_calls': 0}
(HERE/'preparation.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print('Prepared one CLI local-only entry probe. No model calls.')
