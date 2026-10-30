import sys,json,hashlib,shutil,re
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone

OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
sys.path.insert(0,str(LAB))
import rtl_lab as lab
EXE=LAB/'exploration/20261024/public-rag-next-executor-v1'
B=LAB/'exploration/20261024/public-rag-next-v1'
RUN=EXE/'runtime/live-run'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def posix_path(p):
    p=p.replace('\\','/')
    return Path('/mnt/'+p[0].lower()+p[2:]) if re.match(r'^[A-Za-z]:/',p) else Path(p)
def source_paths():
    paths=[OUT/'run.py',OUT/'PLAN.md',LAB/'rtl_lab.py',B/'packet-lock.json',EXE/'source-lock.json',EXE/'input-lock.json']
    for lock,base in [(B/'packet-lock.json',B),(EXE/'source-lock.json',EXE),(EXE/'input-lock.json',None)]:
        for n,h in read(lock).items():
            p=base/n if base else posix_path(n)
            assert sha(p)==h,(str(p),'prior lock mismatch')
            paths.append(p)
    for s in read(B/'C/slots.json'):
        paths.append(RUN/'results'/f'{s["id"]}.json')
        for n in ['dut.sv','reference.sv','testbench.sv']:
            paths.append(RUN/'jobs'/f'{s["ordinal"]:03d}'/n)
    for name in ['yosys','iverilog','vvp']:
        p=shutil.which(name);assert p,name; paths.append(Path(p))
    return {str(p):sha(p) for p in paths}
def execute(argv,folder,stage,timeout):
    result=lab.run_process(argv,folder,timeout)
    lab.save_process(folder,stage,result)
    if result['timeout'] or result['output_limit']:
        raise RuntimeError(stage+' resource/timeout stop')
    return result
def simulate(d,source,label):
    binary=label+'.vvp'
    comp=execute(['/usr/bin/iverilog','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o',binary,source,'testbench.sv','reference.sv'],d,label+'-compile',15)
    if comp['returncode']:return dict(status='COMPILE_ERROR')
    sim=execute(['/usr/bin/vvp',binary],d,label+'-simulate',10)
    matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$', '\n'.join(sim['stdout'].splitlines()),re.M)
    if sim['returncode'] or len(matches)!=1 or 'TIMEOUT' in sim['stdout'].upper():
        raise RuntimeError(label+' simulation failed or invalid summary')
    n,t=map(int,matches[0]);assert t>0
    return dict(status='PASS' if n==0 else 'FAIL',mismatches=n,samples=t)
def main():
    if sys.argv[1]=='prepare':
        assert not (OUT/'input-lock.json').exists()
        save(OUT/'input-lock.json',source_paths());print('Inputs and tools frozen; zero EDA/model calls.');return
    assert sys.argv[1]=='run'
    frozen=read(OUT/'input-lock.json')
    assert source_paths()==frozen
    jobs=OUT/'jobs';jobs.mkdir(exist_ok=False)
    toolinfo={}
    for tool in ['yosys','iverilog','vvp']:
        r=execute(['/usr/bin/'+tool,'-V'],OUT,tool+'-version',10)
        assert r['returncode']==0
        toolinfo[tool]=dict(sha256=sha('/usr/bin/'+tool),version=(r['stdout']+r['stderr']).splitlines()[0])
    save(OUT/'environment.json',dict(tools=toolinfo,process_runner_sha256=sha(LAB/'rtl_lab.py'),flow='generic synth-noabc; original TB on RTL and netlist'))
    slots=read(B/'C/slots.json');assert len(slots)==96
    rows=[]
    for s in slots:
        d=jobs/f'{s["ordinal"]:03d}';d.mkdir()
        origin=RUN/'jobs'/f'{s["ordinal"]:03d}'
        r=read(RUN/'results'/f'{s["id"]}.json')
        row={k:s[k] for k in ['ordinal','id','task','condition','model','sample']}
        row.update(original_status=r['status'],original_receipt=r['receipt'],original_result_sha256=sha(RUN/'results'/f'{s["id"]}.json'))
        for name in ['dut.sv','reference.sv','testbench.sv']:
            (d/name).write_bytes((origin/name).read_bytes())
        row['rtl_sha256']=sha(d/'dut.sv')
        row['rtl_simulation']=simulate(d,'dut.sv','rtl')
        (d/'synthesis.ys').write_text('read_verilog -sv dut.sv\nhierarchy -check -top TopModule\nproc\ncheck -assert\nsynth -noabc -top TopModule\ncheck -assert\ntee -o stat.json stat -json\nwrite_json netlist.json\nwrite_verilog -noattr netlist.v\n',encoding='utf-8')
        sr=execute(['/usr/bin/yosys','-T','-s','synthesis.ys'],d,'synthesis',60)
        row['synthesis_status']='SYNTH_PASS' if sr['returncode']==0 else 'SYNTH_FAIL'
        if sr['returncode']==0:
            mod=read(d/'stat.json')['modules']['\\TopModule'];cells=mod['num_cells_by_type']
            row.update(generic_cells=mod['num_cells'],cell_types=cells,latches=sum(n for k,n in cells.items() if 'LATCH' in k.upper()),netlist_sha256=sha(d/'netlist.v'))
            row['netlist_simulation']=simulate(d,'netlist.v','netlist')
        else:row['netlist_simulation']=dict(status='NOT_RUN')
        row['matches_original']=row['rtl_simulation'].get('mismatches')==r['receipt'][0][0] and row['rtl_simulation'].get('samples')==r['receipt'][0][1]
        row['matches_rtl']=row['rtl_simulation']==row['netlist_simulation']
        save(d/'result.json',row);rows.append(row)
        if s['ordinal']%12==0:print('Completed '+str(s['ordinal'])+'/96',flush=True)
    assert all(sha(p)==h for p,h in frozen.items())
    summary=dict(utc=datetime.now(timezone.utc).isoformat(),model_calls=0,planned=96,completed=len(rows),synthesis_counts=dict(Counter(r['synthesis_status'] for r in rows)),rtl_sim_counts=dict(Counter(r['rtl_simulation']['status'] for r in rows)),netlist_sim_counts=dict(Counter(r['netlist_simulation']['status'] for r in rows)),cross_platform_matches=sum(r['matches_original'] for r in rows),rtl_netlist_matches=sum(r['matches_rtl'] for r in rows),latch_samples=sum(r.get('latches',0)>0 for r in rows),inputs_unchanged=True,rows=rows)
    save(OUT/'summary.json',summary)
    save(OUT/'evidence-lock.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}))
if __name__=='__main__':
    try: main()
    except Exception as e:
        save(OUT/'STOP.json',dict(error=str(e),utc=datetime.now(timezone.utc).isoformat(),no_retry=True));raise
