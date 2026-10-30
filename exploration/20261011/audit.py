"""Read-only provenance checks, independent witness checks, source snapshots."""
import sys,json,itertools,shutil
from pathlib import Path
from collections import Counter,defaultdict
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import batch,rtl_lab as lab,paired_bank as bank,fsm_ir

def main():
    historical=[]
    for name in ('pilot60','fsm48','paired-a32','paired-b64'):
        folder=ROOT/'evidence'/name
        paths=list((folder/'generated').rglob('*.result.json')) if name=='pilot60' else list((folder/'jobs').glob('*/result.json'))
        rows=[];dups=defaultdict(list)
        for p in paths:
            r=batch.read(p);dut=p.with_name(p.name.replace('.result.json','.sv')) if name=='pilot60' else p.parent/'dut.sv'
            sha=lab.digest(dut.read_bytes()) if dut.exists() else None
            assert sha==r.get('rtl_sha256'),str(p)
            row=dict(path=str(p.relative_to(ROOT)),result_sha256=lab.digest(p.read_bytes()),rtl_sha256=sha,status=r['status'],task=r.get('task'),localization=r.get('localization'))
            rows.append(row)
            if sha:dups[sha].append(row['path'])
        historical.append(dict(experiment=name,result_files=len(paths),retained_rtl=sum(r['rtl_sha256'] is not None for r in rows),statuses=dict(Counter(r['status'] for r in rows)),distinct_rtl_hashes=len(dups),exact_duplicate_clusters=[dict(sha256=h,paths=ps) for h,ps in dups.items() if len(ps)>1],failures=[r for r in rows if r['status']!='PASS'],rows=rows))
    assert [r['retained_rtl'] for r in historical]==[60,24,32,62]
    batch.atomic(HERE/'historical-audit.json',dict(verified_utc=lab.utc(),retained_rtl=178,experiments=historical,limits='File/hash audit of preserved evidence, not a fresh execution or new sample. Exact-byte duplicates only; no semantic independence claim.'))
    audits=[]
    for run in sorted((HERE/'runs').iterdir()):
        if not run.is_dir():continue
        lock=batch.read(run/'evidence-lock.json');files={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
        assert files==set(lock),run
        for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,rel
        plan=batch.read(run/'plan.json')
        for rel,h in plan['source_hashes'].items():
            p=ROOT/rel;assert lab.digest(p.read_bytes())==h,rel
            dest=HERE/'snapshots'/run.name/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert lab.digest(dest.read_bytes())==h
            else:shutil.copyfile(p,dest)
        audits.append(dict(run=run.name,verified_files=len(lock),source_files=len(plan['source_hashes']),plan_sha256=lab.digest((run/'plan.json').read_bytes())))
    # Independent brute-force enumeration below the delayed witness length.
    # Uses procedural oracle, not product_check or the reference graph.
    short=[]
    for case in batch.read(HERE/'runs/delayed-v1/cases.json'):
        ir=fsm_ir.parse(json.dumps(case['ir']));task=case['task'];count=0
        for n in range(12):
            for word in itertools.product((0,1),repeat=n):
                state=ir['reset']['state'];outputs=[]
                for bit in word:
                    state=ir['edges'][state,bit];outputs.append(ir['outputs'][state])
                expected=[r[3] for r in bank.oracle(task,[(0,0)]+[(1,b) for b in word])][1:]
                assert outputs==expected
                assert ir['outputs'][ir['reset']['state']]==bank.oracle(task,[(0,0)])[0][3]
                count+=1
        word=case['word'];observed=fsm_ir.trace(ir,word);expected=[r[3] for r in bank.oracle(task,[(0,0)]+[(1,int(b)) for b in word])][1:]
        assert observed[:-1]==expected[:-1] and observed[-1]!=expected[-1]
        short.append(dict(task=task,shorter_sequences_checked=count,witness=word,observed=observed,expected=expected,shortest_length=12))
    formal=[]
    for case in batch.read(HERE/'runs/delayed-v1/cases.json'):
        trace=batch.read(HERE/'runs/formal-v1'/case['task']/'trace.json')
        waves={s['name']:s['wave'] for s in trace['signal']}
        def decode(wave):
            values=[];last=None
            for c in wave:
                if c in '01':last=int(c)
                elif c!='.':last=None
                values.append(last)
            return values
        din=decode(waves['din']);rst=decode(waves['rst_n']);mismatch=decode(waves['mismatch'])
        assert rst[1]==0 and all(v==1 for v in rst[2:])
        assert ''.join(str(b) for b in din[2:14])==case['word']
        assert 1 in mismatch
        formal.append(dict(task=case['task'],solver_prefix=case['word'],mismatch_step=mismatch.index(1),note='Yosys state/output at timestep reflects prior timestep transition; prefix inputs step2..13, mismatch step14.'))
    batch.atomic(HERE/'verification.json',dict(status='PASS',runs=audits,independent_shortest_witness_checks=short,formal_trace_checks=formal,notes='No runner changes; no broad core regression needed. Existing paired_audit and mutation verify independently passed.'))
    print(json.dumps(dict(history=[dict(experiment=r['experiment'],rtl=r['retained_rtl'],status=r['statuses'],distinct_hashes=r['distinct_rtl_hashes']) for r in historical],new_runs=audits,independent_shorter_sequences=sum(r['shorter_sequences_checked'] for r in short)),indent=2))
if __name__=='__main__':main()
