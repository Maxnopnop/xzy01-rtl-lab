"""Read-only evidence verification; compare event expectations to frozen graph."""
import sys,json
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import batch,rtl_lab as lab,paired_bank as bank,fsm_ir

def main():
    locks=[]
    for name in ('compound-v1','delayed-v1','factorial20-v1','formal-v1','r1b-v1','r1b-v2','timed-reset-v1','timed-calibration-v1','timed-calibration-v2'):
        run=HERE/'runs'/name;lock=batch.read(run/'evidence-lock.json')
        assert {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}==set(lock)
        for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(name,rel)
        for rel,h in batch.read(run/'plan.json')['source_hashes'].items():assert lab.digest((ROOT/rel).read_bytes())==h,(name,rel)
        locks.append(dict(run=name,files=len(lock)))
    run=HERE/'runs/timed-reset-v1';profiles=batch.read(run/'events.json');counts={};checks=0
    for task,rows in profiles.items():
        ir=fsm_ir.parse((bank.ROOT/task/'reference.json').read_text());state=ir['reset']['state'];lastclk=0
        for e in rows:
            if not e['reset']:state=ir['reset']['state']
            elif e['clk'] and not lastclk:state=ir['edges'][state,e['bit']]
            assert e['expected']==ir['outputs'][state],(task,e)
            lastclk=e['clk'];checks+=1
        counts[task]=dict(Counter(e['category'] for e in rows))
    selected=batch.read(run/'selection.json');results=batch.read(run/'history-results.json');assert len(results)==64
    for row,item in zip(results,selected['rows']):
        assert row['source']==item and item['original_status']=='PASS'
        folder=run/'history'/f'{row["selection_index"]:02d}_{item["task"]}'
        assert (folder/'dut.sv').read_bytes()==(ROOT/item['dut_path']).read_bytes()
        assert lab.digest((ROOT/item['result_path']).read_bytes())==item['result_sha256']
        r=row['result'];assert r['status']=='PASS'
        assert (folder/'verdict.txt').read_text().strip()=='RTL_LAB_V1 '+r['receipt_nonce']+' checks='+str(len(profiles[item['task']]))+' errors=0'
    cal=batch.read(run/'calibration.json');assert len(cal)==10 and all(c['status']==c['expected'] for c in cal)
    out=dict(status='PASS',old_locks=locks,event_graph_crosschecks=checks,event_categories=counts,
             historical_byte_bindings=64,distinct_selected_hashes=len({r['rtl_sha256'] for r in selected['rows']}),
             available_distinct_hashes=selected['distinct_hashes'],available_records=selected['total_original_pass_records'],
             task_model_counts=dict(Counter(r['task']+' / '+r['model'] for r in selected['rows'])),
             calibration_first_mismatches={c['label']:c.get('mismatches',[])[:1] for c in cal},
             limits='Graph crosscheck is separate from sequence oracle and handcoded RTL, but shares the frozen specification.')
    batch.atomic(HERE/'r1c-verification.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
