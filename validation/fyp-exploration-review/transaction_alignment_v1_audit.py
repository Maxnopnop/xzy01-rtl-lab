"""Coordinator read-only arithmetic audit. Never import/run target or EDA tools."""
import hashlib
import json
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'exploration/20261015/transaction-alignment-v1'
RUN = PACK / 'run-v1'
PLAN_SHA = 'c2aeef0482f72c1deded6bf45d6aae6012a889dc4f71801a633e4aa04e942c10'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def source_plan(scene):
    if scene in (0, 4):
        return [[[17+i, int(i == 2)] for i in range(3)],
                [[161+i, int(i == 2)] for i in range(3)]]
    if scene == 1:
        return [[[32+i, int(i == 7)] for i in range(8)]]
    if scene in (2, 3):
        return [[[81, 1]]]
    return [[[17+i, int(i == 2)] for i in range(3)]]

def decode(value, fields):
    result = {}
    for name, width in reversed(fields):
        result[name] = value & ((1 << width)-1)
        value >>= width
    assert value == 0
    return result

INPUTS = [('s_valid',1), ('s_data',8), ('s_last',1), ('m_ready0',1), ('m_ready1',1)]
OUTPUTS = [('s_ready',1), ('m_valid0',1), ('m_data0',8), ('m_last0',1), ('m_valid1',1), ('m_data1',8), ('m_last1',1)]

def raw_events(path):
    events = []
    def number(s, base):
        return s if any(x in s.lower() for x in 'xz') else int(s, base)
    for k, line in enumerate(path.read_text().splitlines()):
        t = line.split()
        assert len(t) == 16
        assert [int(t[0]), t[1]] == [k//2, 'POST' if k % 2 else 'PRE']
        endpoints = [dict(valid=number(t[i],2), ready=number(t[i+1],2), data=number(t[i+2],16), last=number(t[i+3],2)) for i in (4,8,12)]
        events.append(dict(cycle=int(t[0]), phase=t[1], rst=1-int(t[2]), offer_index=int(t[3]), s=endpoints[0], m=endpoints[1:]))
    assert len(events) == 160
    return events

def recompute(rows, scene):
    # Independently derive receipt queues, delivery IDs, hold obligations and reset cancellations.
    if [r['cycle'] for r in rows] != list(range(80)):
        return 'TRACE_INVALID', None, None
    plans = source_plan(scene)
    errors = Counter()
    queues = [deque(), deque()]
    holds = [None, None, None]
    active = False
    epoch = 0
    after_reset = False
    seen = [0] * len(plans)
    accepted, deliveries, cancellations = [], [[], []], []
    spec_accepted, spec_deliveries, aborted = [], [[], []], []
    for r in rows:
        cycle = r['cycle']
        if r['rst']:
            if active:
                assert len(plans) == 2 and epoch == 0
                cancellations.append(dict(epoch=epoch, pending=[[t['id'] for t in q] for q in queues]))
                aborted.append(dict(epoch=epoch, cycle=cycle, pending=[len(q) for q in queues], unaccepted=len(plans[epoch])-seen[epoch]))
                queues = [deque(), deque()]
                holds = [None, None, None]
                active = False
                after_reset = True
            continue
        if after_reset:
            epoch += 1
            after_reset = False
        active = True
        for i, e in enumerate([r['s']] + r['m']):
            assert type(e['valid']) is int and e['valid'] in (0,1)
            assert type(e['ready']) is int and e['ready'] in (0,1)
            beat = [e['data'], e['last']] if e['valid'] else None
            if beat is not None:
                assert type(beat[0]) is int and 0 <= beat[0] <= 255 and beat[1] in (0,1)
            if holds[i] is not None and beat != holds[i]:
                errors['INPUT_PROTOCOL_FAIL' if i == 0 else 'BACKPRESSURE_FAIL'] += 1
            holds[i] = beat if e['valid'] and not e['ready'] else None
        s = r['s']
        if s['valid'] and s['ready']:
            beat = [s['data'], s['last']]
            assert r['offer_id'] == [epoch, seen[epoch]]
            if seen[epoch] >= len(plans[epoch]) or beat != plans[epoch][seen[epoch]]:
                errors['INPUT_PROTOCOL_FAIL'] += 1
            seen[epoch] += 1
            token = dict(id=r['offer_id'], beat=beat, cycle=cycle)
            accepted.append(token)
            spec_accepted.append(dict(epoch=epoch, cycle=cycle, beat=beat))
            for q in queues:
                q.append(token)
        for i, e in enumerate(r['m']):
            if e['valid'] and e['ready']:
                beat = [e['data'], e['last']]
                token = queues[i].popleft() if queues[i] else None
                if token is None:
                    errors['UNEXPECTED_TRANSACTION'] += 1
                elif beat != token['beat']:
                    errors['DATA_OR_ORDER_FAIL'] += 1
                deliveries[i].append(dict(id=token['id'] if token else None, beat=beat, cycle=cycle, source_cycle=token['cycle'] if token else None))
                spec_deliveries[i].append(dict(epoch=epoch, cycle=cycle, beat=beat))
    assert active and epoch == len(plans)-1
    assert all(all(m['ready'] for m in row['m']) for row in rows[-8:])
    if seen[epoch] < len(plans[epoch]):
        errors['LIVENESS_FAIL'] += 1
    for q in queues:
        if q:
            errors['MISSING_TRANSACTION'] += 1
    for cancellation in cancellations:
        e = cancellation['epoch']
        used = {tuple(t['id']) for t in accepted if t['id'][0] == e}
        cancellation['unaccepted'] = [[e,i] for i in range(len(plans[e])) if (e,i) not in used]
    status = 'INPUT_PROTOCOL_FAIL' if errors['INPUT_PROTOCOL_FAIL'] else 'FUNCTION_FAIL' if errors else 'PASS'
    spec = dict(counts=dict(errors), accepted=spec_accepted, delivered=spec_deliveries, aborted=aborted, source_accepted_per_epoch=seen, pending=[len(q) for q in queues])
    book = dict(accepted=accepted, outputs=deliveries, cancelled=cancellations)
    return status, spec, book

def ir_arithmetic(events, scene):
    # Closed-form one-slot hand mapping; does not evaluate JSON expressions or use target AST.
    data = last = pending = index = 0
    plans = source_plan(scene)
    for cycle in range(80):
        reset = cycle < 3 or scene in (0,4) and cycle in (8,9)
        epoch = int(scene in (0,4) and cycle >= 8)
        beats = plans[epoch]
        payload = beats[index] if index < len(beats) else [0,0]
        if scene == 4 and cycle in (6,7):
            payload = [payload[0] ^ 1, payload[1]]
        ready = (1, int(cycle >= 10)) if scene in (0,4) else (int(cycle >= 7),)*2 if scene == 3 else (1,1)
        inp = dict(s_valid=int(not reset and index < len(beats)), s_data=payload[0], s_last=payload[1], m_ready0=ready[0], m_ready1=ready[1])
        pre_ready = int(pending == 0)
        for phase in range(2):
            ev = events[cycle*2+phase]
            assert (ev['cycle'],ev['phase'],ev['offer_id']) == (cycle,'POST' if phase else 'PRE',[epoch,index])
            assert ev['input_event']['clk'] == phase and ev['input_event']['rst_n'] == int(not reset)
            assert decode(ev['input_event']['input'], INPUTS) == inp
            if phase:
                if reset:
                    data = last = pending = 0
                elif pending == 0 and inp['s_valid']:
                    data, last, pending = inp['s_data'], inp['s_last'], 3
                else:
                    pending &= 3 ^ (ready[0] | ready[1] << 1)
            expected = dict(s_ready=int(pending == 0), m_valid0=pending & 1, m_data0=data, m_last0=last, m_valid1=pending >> 1 & 1, m_data1=data, m_last1=last)
            assert ev['outputs'] == expected == decode(ev['packed_output'], OUTPUTS)
        if reset:
            index = 0
        elif inp['s_valid'] and pre_ready:
            index += 1

def main():
    plan=read(PACK/'plan.json');assert sha(PACK/'plan.json') == PLAN_SHA
    for n,h in plan['source_hashes'].items():
        assert sha(PACK/n)==h,n
    prior=read(PACK/'prior-lock.json')
    for n,h in prior.items():
        assert sha(ROOT/n)==h,n
    lock=read(RUN/'evidence-lock.json')
    assert set(lock)=={p.relative_to(RUN).as_posix() for p in RUN.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
    for n,h in lock.items():
        assert sha(RUN/n)==h,n
    summary=read(RUN/'summary.json')
    assert summary['plan_sha256']==PLAN_SHA and summary['pending']==[] and summary['model_calls']==0
    assert summary['actual_calls']==dict(ir=11,compile=11,sim=11)
    assert summary['status']=='COMPLETED_EXPECTATIONS_MATCHED'
    executed=[]; axes={axis:Counter() for axis in ('ir_spec','rtl_spec','intent')}; details={}
    for case in plan['cases']:
        folder=RUN/case['id'];result=read(folder/'result.json')
        if case.get('skip'):
            assert not result['executed'] and not list(folder.glob('*-receipt.json'))
            continue
        executed.append(case['id'])
        for name,seconds in [('ir',30),('compile',15),('sim',10)]:
            started=read(folder/(name+'-started.json'));receipt=read(folder/(name+'-receipt.json'))
            assert all(receipt[k]==v for k,v in started.items())
            assert receipt['returncode']==0 and not receipt['timeout'] and receipt['timeout_seconds']==seconds
            assert sha(Path(receipt['argv'][0]))==receipt['executable_sha256']
            assert Path(receipt['cwd']).resolve()==folder.resolve()
            assert (folder/(name+'.stdout.bin')).exists() and (folder/(name+'.stderr.bin')).exists()
        argv=read(folder/'compile-receipt.json')['argv']
        for param,key in [('KIND','kind'),('SCENE','scene'),('FAULT','fault'),('LATENCY','latency')]:
            assert '-Ptb.'+param+'='+str(case[key]) in argv
        assert (folder/'sim.vvp').stat().st_size>0
        assert 'rows=160 cycles=80' in (folder/'sim.stdout.bin').read_text()
        ev=raw_events(folder/'trace.txt');assert ev==read(folder/'native-normalized-events.json')
        native=[dict(cycle=e['cycle'],rst=e['rst'],s=e['s'],m=e['m'],offer_id=[int(case['scene'] in (0,4) and e['cycle']>=8),e['offer_index']]) for e in ev if e['phase']=='PRE']
        assert native==read(folder/'native-pre-full.json')
        view=[r for r in native if r['cycle']!=case.get('drop_rtl_cycle',-1)]
        assert view==read(folder/'native-assessment-view.json')
        irevents=read(folder/'ir-events.json');assert len(irevents)==160
        ir_arithmetic(irevents,case['scene'])
        irrows=read(folder/'ir-pre.json');assert len(irrows)==80
        for e,row in zip(irevents[::2],irrows):
            v=decode(e['input_event']['input'],INPUTS);o=e['outputs']
            assert row==dict(cycle=e['cycle'],rst=1-e['input_event']['rst_n'],offer_id=e['offer_id'],s=dict(valid=v['s_valid'],ready=o['s_ready'],data=v['s_data'],last=v['s_last']),m=[dict(valid=o[f'm_valid{i}'],ready=v[f'm_ready{i}'],data=o[f'm_data{i}'],last=o[f'm_last{i}']) for i in range(2)])
        books=[];statuses=[];counts=[]
        for rows,label in [(irrows,'ir'),(view,'rtl')]:
            status,spec,book=recompute(rows,case['scene']);saved=read(folder/(label+'-assessment.json'))
            assert status==saved['spec']['status'] and book==saved['ledger'],(case['id'],label)
            if spec is not None:
                for k,v in spec.items():assert saved['spec'][k]==v,(case['id'],label,k)
            books.append(book);statuses.append(status);counts.append(spec['counts'] if spec else {})
        if any(s in ('TRACE_INVALID','INPUT_PROTOCOL_FAIL') for s in statuses):
            relation='NOT_EVALUABLE'
        elif [t['id'] for t in books[0]['accepted']]!=[t['id'] for t in books[1]['accepted']] or books[0]['cancelled']!=books[1]['cancelled']:
            relation='NOT_EVALUABLE'
        elif any(set(c)&{'UNEXPECTED_TRANSACTION','BACKPRESSURE_FAIL','MISSING_TRANSACTION','LIVENESS_FAIL'} for c in counts):
            relation='FUNCTION_FAIL'
        else:
            transcripts=[[[[t['id'],t['beat']] for t in sink] for sink in b['outputs']] for b in books]
            relation='PASS' if transcripts[0]==transcripts[1] else 'FUNCTION_FAIL'
        observed=dict(ir_spec=statuses[0],rtl_spec=statuses[1],intent=relation)
        assert observed==result['observed']==case['expected']
        assert relation==read(folder/'intent-assessment.json')['status']
        for k,v in observed.items():axes[k][v]+=1
        if case['id'] in ('01_same_mapping','07_partial_delivery_reset'):
            for x,y in zip(irevents,ev):
                o=x['outputs'];assert [y['s']['ready']]+[m[k] for m in y['m'] for k in ('valid','data','last')]==[o[k] for k,w in OUTPUTS]
        details[case['id']]=dict(observed=observed,ir_accept_cycles=[t['cycle'] for t in books[0]['accepted']] if books[0] else None,rtl_accept_cycles=[t['cycle'] for t in books[1]['accepted']] if books[1] else None,rtl_counts=counts[1],ir_cancelled=books[0]['cancelled'] if books[0] else None,rtl_cancelled=books[1]['cancelled'] if books[1] else None)
    assert len(executed)==11
    report=dict(status='ACCEPTED_FINITE_DEVELOPMENT_TRANSACTION_ALIGNMENT',plan_sha256=PLAN_SHA,source_bindings=len(plan['source_hashes']),prior_bindings=len(prior),run_bindings=len(lock),denominator=12,executed_pairs=11,preclassified_unexecuted=1,actual_calls=summary['actual_calls'],model_calls=0,executed_axes={k:dict(v) for k,v in axes.items()},raw_native_events=1760,ir_events_independently_recomputed=1760,same_mapping_phase_comparisons=320,case_details=details,review_method='Own read-only raw normalization, closed-form slot arithmetic, temporal queue/hold/reset ledger and receipt/hash checks; no target modules imported or IR/EDA reruns',external_preparation_readiness='YES for separately authorized bounded source/contract screening; no source or model release',limitations=['Synthetic same-author development fixtures; no natural model benefit or cognitive-stage attribution','Original batch-run versus inserted-yield runtime equivalence not directly replayed','Restricted witnesses and bounded sync-reset coverage; no physical release timing','Tool transitive dependencies incomplete; default regression failures preserved'])
    out=ROOT/'validation/fyp-exploration-review/transaction-alignment-v1-completion-coordinator-audit.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='case_details'},ensure_ascii=False))

if __name__=='__main__':
    main()
