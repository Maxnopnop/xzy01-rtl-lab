"""Unchanged usage_record from audited prior source; no payload adaptation."""
import copy
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
