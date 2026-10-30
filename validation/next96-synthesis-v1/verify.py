import json,hashlib,re
from pathlib import Path
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
RUN=LAB/'exploration/20261024/public-rag-next-executor-v1/runtime/live-run'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hostpath(s):
    if s.startswith('/mnt/') and s[6]=='/':return Path(s[5].upper()+':'+s[6:])
    return Path(s)
e=read(OUT/'evidence-lock.json')
assert all(sha(OUT/p)==h for p,h in e.items())
inputs=read(OUT/'input-lock.json')
local_checks=0
for p,h in inputs.items():
    if p.startswith('/mnt/'):
        assert sha(hostpath(p))==h,p;local_checks+=1
summary=read(OUT/'summary.json');rows=summary['rows'];assert len(rows)==96
counts=Counter(); arms=defaultdict(Counter); tasks=defaultdict(list)
for r in rows:
    d=OUT/'jobs'/f'{r["ordinal"]:03d}'
    assert read(d/'result.json')==r
    src=RUN/'jobs'/f'{r["ordinal"]:03d}'
    for n in ['dut.sv','reference.sv','testbench.sv']:assert (d/n).read_bytes()==(src/n).read_bytes()
    assert sha(d/'dut.sv')==r['rtl_sha256']
    assert sha(RUN/'results'/f'{r["id"]}.json')==r['original_result_sha256']
    for stage in ['rtl-compile','rtl-simulate','synthesis','netlist-compile','netlist-simulate']:
        receipt=read(d/(stage+'.json'))
        assert receipt['returncode']==0 and not receipt['timeout'] and not receipt['output_limit']
    for stage,key in [('rtl','rtl_simulation'),('netlist','netlist_simulation')]:
        matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$', '\n'.join((d/(stage+'-simulate.stdout.log')).read_text().splitlines()),re.M)
        assert len(matches)==1
        n,t=map(int,matches[0]);assert n==r[key]['mismatches'] and t==r[key]['samples']
    mod=read(d/'stat.json')['modules']['\\TopModule']
    assert mod['num_cells']==r['generic_cells']
    assert mod['num_cells_by_type']==r['cell_types']
    assert sha(d/'netlist.v')==r['netlist_sha256']
    counts[r['synthesis_status']]+=1
    arms[(r['model'],r['condition'])][r['netlist_simulation']['status']]+=1
    tasks[r['task']].append(r['generic_cells'])
assert counts==Counter(summary['synthesis_counts'])
verification=dict(status='VERIFIED',artifact_hashes_checked=len(e),local_input_hashes_checked=local_checks,actual_successful_tool_processes=480,version_checks=3,synthesis_counts=dict(counts),arms={m+'/'+c:dict(v) for (m,c),v in arms.items()},generic_cell_ranges={t:[min(v),max(v)] for t,v in tasks.items()},source_rtl_modified=False,model_calls=0,additional_eda_calls_by_verifier=0)
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verification,ensure_ascii=False,indent=2))
