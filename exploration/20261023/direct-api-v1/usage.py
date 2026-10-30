"""Offline payload/accounting adaptation only. No transport or production entrypoint."""
import copy
import hashlib
import json

MODELS = ('gpt-5.6-luna', 'gpt-5.6-terra', 'gpt-5.6-sol')

def adapt_request(raw: bytes, expected_sha256: str):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Frozen request hash mismatch')
    old = json.loads(raw.decode('utf-8'))
    if old.get('model') not in MODELS or old.get('max_completion_tokens') != 8192:
        raise ValueError('Unexpected original model or budget')
    if [m.get('role') for m in old['messages']] != ['system', 'user']:
        raise ValueError('Unexpected frozen roles')
    if any(k in old for k in ('reasoning', 'reasoning_effort', 'temperature', 'seed')):
        raise ValueError('Original optional sampling fields must remain omitted')
    revised = copy.deepcopy(old)
    del revised['max_completion_tokens']
    return revised

def usage_record(raw):
    """Normalize only explicit numeric fields; never infer unknown usage or costs."""
    source = copy.deepcopy(raw)
    obj = raw if isinstance(raw, dict) else {}
    def number(value):
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    def pick(*values):
        for value in values:
            parsed = number(value)
            if parsed is not None:
                return parsed
        return None
    def details(name):
        value = obj.get(name)
        return value if isinstance(value, dict) else {}
    values = {
        'input_tokens': pick(obj.get('input_tokens'), obj.get('prompt_tokens')),
        'output_tokens': pick(obj.get('output_tokens'), obj.get('completion_tokens')),
        'reasoning_tokens': pick(details('output_tokens_details').get('reasoning_tokens'), details('completion_tokens_details').get('reasoning_tokens')),
        'cached_input_tokens': pick(obj.get('cached_input_tokens'), details('input_tokens_details').get('cached_tokens'), details('prompt_tokens_details').get('cached_tokens')),
        'total_tokens': number(obj.get('total_tokens')),
    }
    return {'values': values, 'unknown_fields': [k for k,v in values.items() if v is None], 'raw_usage': source,
            'cost': None, 'reasoning_is_not_added_to_output': True}

def execution_decision(prompt_gate, production_retry_gate, coordinator_review):
    """Advisory gate only; this module cannot execute even if booleans are true."""
    return {'eligible_for_separate_dispatcher_review': all((prompt_gate, production_retry_gate, coordinator_review)),
            'transport_implemented': False, 'starts_calls': False}
