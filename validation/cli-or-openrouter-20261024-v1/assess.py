"""Read-only assessment of the one local CLI capture and existing API evidence."""
import hashlib
import json
from pathlib import Path
from collections import Counter

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
API = ROOT/'exploration/20261023/direct-api-v1'
OLD = ROOT/'exploration/20261023/cli-cache-repair-v1'
PACKET = ROOT/'exploration/20261023/public-rag-all20-v1'
evidence = {}
def read(p):
    raw = p.read_bytes()
    evidence[str(p)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw.decode('utf-8-sig'))
def lock(p, base=None):
    data = read(p)
    mismatches = []
    for name, expected in data.items():
        file = base/name if base else Path(name)
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        evidence[str(file)] = actual
        if actual != expected:
            mismatches.append(str(file))
    assert not mismatches, mismatches
    return {'count': len(data), 'all_match': True}

receipt = read(OUT/'local-tests-candidate2/probe-gpt-5.6-luna/receipt.json')
capture = read(OUT/'local-tests-candidate2/probe-gpt-5.6-luna/request-1.bin')
messages = read(PACKET/'messages/Prob023_vector100r__no_rag.json')
def message_text(message):
    content = message.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(part.get('text','') for part in content)
    return ''
items = capture['input']
normalized = [{'role': item.get('role'), 'content': message_text(item)} for item in items]
old_plan = read(OLD/'local-tests-candidate2/predeclared-plan.json')
binary = Path(old_plan['binary'])
binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
evidence[str(binary)] = binary_sha
api_locks = {'source': lock(API/'source-lock.json', API), 'input': lock(API/'input-lock.json')}
old_gate = read(API/'gate-tests/summary.json')
old_audit = read(ROOT/'validation/openrouter-coordinator-review-v1/client-audit.json')
final_audit = read(ROOT/'validation/openrouter-final240-audit-v1/audit.json')
rows = [read(p) for p in sorted((ROOT/'validation/openrouter-resume198-v1/runtime/continuation/results').glob('*.json'))]
assert len(rows) == len({r['slot'] for r in rows}) == 240
result = {
    'decision': 'CLI_ENTRY_RECHECK_BLOCKED_OPENROUTER_SELECTED_FOR_FUTURE_PREPARATION',
    'new_model_calls': 0, 'new_formal_reservations': 0, 'new_cli_launches': 1,
    'new_local_mock_posts': receipt['posts'], 'cli_receipt': receipt,
    'cli_binary_same_as_previous_audit': binary_sha == old_plan['binary_sha256'],
    'cli_input_roles': [i.get('role') for i in items],
    'frozen_message_roles': [m['role'] for m in messages],
    'cli_visible_messages_equal_frozen': normalized == messages,
    'last_user_original_body_equal': normalized[-1]['content'] == messages[-1]['content'],
    'cli_top_level_fields': list(capture), 'cli_reasoning': capture.get('reasoning'),
    'cli_three_model_equality': 'NOT_EXECUTED_STOPPED_AT_FIRST_GATE',
    'cli_zero_retry_matrix': 'NOT_EXECUTED_EARLY_STOP_NOT_PROVEN',
    'api_locks': api_locks,
    'historical_api_gate_checks': {'count': len(old_gate['checks']), 'passed': old_gate['passed'], 'rerun_this_turn': False},
    'historical_api_mock_matrix_cases': old_audit['checks']['matrix_raw_ledger_cases'],
    'api_completed_slots': len(rows), 'api_completed_counts': dict(Counter(r['status'] for r in rows)),
    'historical_final_wire_verified': final_audit['all_new_wire_and_model_provider_verified'],
    'limits': [
        'Only local custom-provider CLI path probed. Logged-in production path not proven.',
        'Proxy denied observed background GET; not an OS-wide firewall audit.',
        'Early stop means one observed POST does not certify zero retries.',
        'API historic successful calls do not certify current balance, account access or model availability.',
        'API client invariants cannot establish unobservable gateway/provider internals.',
        'No permission inferred to repeat finished slots, failures, create new prompts, or launch a new model batch.'
    ]
}
assert result['last_user_original_body_equal']
assert not result['cli_visible_messages_equal_frozen']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in evidence.items())
result['read_evidence_unchanged'] = True
for name, obj in [('assessment.json',result),('evidence-lock.json',evidence)]:
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['decision','new_cli_launches','new_local_mock_posts','cli_input_roles','last_user_original_body_equal','api_locks','api_completed_slots','read_evidence_unchanged']},ensure_ascii=False))
