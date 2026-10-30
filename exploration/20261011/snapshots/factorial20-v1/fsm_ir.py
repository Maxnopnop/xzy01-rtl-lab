"""Bounded, data-only Moore FSM interpreter. No generated code is executed."""
from collections import deque
import json
import re


SCHEMA_TEXT = '''Return only JSON (no RTL) with exactly these fields:
{"schema":1,"clock_edge":"posedge","output_kind":"moore",
 "reset":{"kind":"async","active":0,"state":"S0"},
 "states":[{"name":"S0","output":0}],
 "transitions":[{"from":"S0","input":0,"to":"S0"},
                {"from":"S0","input":1,"to":"S0"}]}
This is a schema illustration, NOT the solution. Set reset polarity, reset state,
states, outputs and transitions from the specification. reset.kind can be async
or sync. List every state and exactly one transition per state/input bit.
Use 1..32 states, identifier names, literal 0/1 outputs and inputs.
The output is the output of the state reached after the active edge.
Do not include conditions, expressions, extra keys, or prose.'''


def _object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('Duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def _keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError('Invalid fields in ' + label)


def _bit(value):
    return type(value) is int and value in (0, 1)


def parse(raw):
    if len(raw.encode('utf-8')) > 32768:
        raise ValueError('IR exceeds 32 KiB')
    raw = raw.strip()
    if raw.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', raw, re.S)
        if not match:
            raise ValueError('Expected one JSON block')
        raw = match[1]
    try:
        obj = json.loads(raw, object_pairs_hook=_object)
    except (ValueError, RecursionError) as exc:
        raise ValueError('Invalid JSON: ' + str(exc)[:200]) from None
    _keys(obj, 'schema clock_edge output_kind reset states transitions', 'IR')
    if type(obj['schema']) is not int or obj['schema'] != 1:
        raise ValueError('Unsupported schema')
    if obj['clock_edge'] != 'posedge' or obj['output_kind'] != 'moore':
        raise ValueError('Interpreter supports only posedge, Moore, single-bit FSMs')
    reset = obj['reset']
    _keys(reset, 'kind active state', 'reset')
    if reset['kind'] not in ('async', 'sync') or not _bit(reset['active']):
        raise ValueError('Invalid reset metadata')
    states = obj['states']
    if not isinstance(states, list) or not 1 <= len(states) <= 32:
        raise ValueError('Expected 1..32 states')
    outputs = {}
    for state in states:
        _keys(state, 'name output', 'state')
        name = state['name']
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,31}', name):
            raise ValueError('Invalid state name')
        if name in outputs or not _bit(state['output']):
            raise ValueError('Duplicate state or invalid Moore output')
        outputs[name] = state['output']
    if not isinstance(reset['state'], str) or reset['state'] not in outputs:
        raise ValueError('Missing reset state')
    transitions = obj['transitions']
    if not isinstance(transitions, list) or len(transitions) != 2 * len(states):
        raise ValueError('Expected two transitions per state')
    edges = {}
    for edge in transitions:
        _keys(edge, 'from input to', 'transition')
        if not all(isinstance(edge[k], str) and edge[k] in outputs for k in ('from', 'to')) or not _bit(edge['input']):
            raise ValueError('Invalid transition endpoint/input')
        key = (edge['from'], edge['input'])
        if key in edges:
            raise ValueError('Duplicate transition')
        edges[key] = edge['to']
    return dict(data=obj, outputs=outputs, edges=edges, reset=reset)


def trace(ir, bits):
    state = ir['reset']['state']
    outputs = []
    for bit in bits:
        state = ir['edges'][state, int(bit)]
        outputs.append(ir['outputs'][state])
    return outputs


def product_check(candidate, reference):
    """Exact abstract Moore equivalence from reset; state names are irrelevant.

    Reset metadata is checked separately as part of the declared contract.
    This proves neither arbitrary RTL equivalence nor analog reset behavior.
    """
    metadata = [k for k in ('kind', 'active') if candidate['reset'][k] != reference['reset'][k]]
    start = (candidate['reset']['state'], reference['reset']['state'])
    queue = deque([(start, '')]); seen = {start}
    mismatch = None
    while queue:
        (a, b), path = queue.popleft()
        if candidate['outputs'][a] != reference['outputs'][b]:
            mismatch = dict(bits=path, expected=reference['outputs'][b], observed=candidate['outputs'][a])
            break
        for bit in (0, 1):
            pair = (candidate['edges'][a, bit], reference['edges'][b, bit])
            if pair not in seen:
                seen.add(pair); queue.append((pair, path + str(bit)))
    return dict(status='IR_SPEC_MISMATCH' if metadata or mismatch else 'IR_EQUIVALENT',
                reset_contract_errors=metadata, shortest_counterexample=mismatch,
                visited_pairs=len(seen), scope='Complete finite abstract Moore graph from reset; not an RTL proof')


def timed_vectors(ir, inputs):
    """Evaluate before/after rising edges, with reset changes while clock=0."""
    state = None
    rows = []
    for reset, bit in inputs:
        active = reset == ir['reset']['active']
        if active and ir['reset']['kind'] == 'async':
            state = ir['reset']['state']
        pre = ir['outputs'][state] if state is not None else None
        if active:
            state = ir['reset']['state']
        elif state is not None:
            state = ir['edges'][state, bit]
        post = ir['outputs'][state] if state is not None else None
        rows.append((reset, bit, pre, post))
    return rows


def localize(ir_status, rtl_status, agreement_status):
    if rtl_status not in ('PASS', 'FUNCTION_FAIL'):
        return 'TOOLCHAIN_' + rtl_status
    if ir_status == 'NO_TABLE':
        return 'NO_TABLE_DIAGNOSIS'
    if ir_status == 'IR_INVALID':
        return 'IR_FORMAT_ERROR'
    if agreement_status not in ('PASS', 'FUNCTION_FAIL'):
        return 'INCONCLUSIVE'
    equivalent = ir_status == 'IR_EQUIVALENT'
    agrees = agreement_status == 'PASS'
    if equivalent and agrees:
        return 'ALL_PASS' if rtl_status == 'PASS' else 'CHECKER_INCONSISTENCY'
    if equivalent:
        return 'IR_TO_RTL_ERROR' if rtl_status == 'FUNCTION_FAIL' else 'CHECKER_INCONSISTENCY'
    if agrees:
        return 'SPEC_TO_IR_ERROR' if rtl_status == 'FUNCTION_FAIL' else 'IR_ERROR_NOT_EXPOSED_BY_RTL_TESTS'
    return 'RTL_CORRECTS_IR_ON_TESTS' if rtl_status == 'PASS' else 'BOTH_DIVERGE'
