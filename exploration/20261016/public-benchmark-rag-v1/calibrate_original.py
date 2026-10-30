"""One bounded original-harness smoke per selected public reference; no model DUTs."""
import hashlib,json,os,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def main():
    run=HERE/'reference-calibration'
    assert not run.exists(),'No calibration retry'
    run.mkdir()
    rows=json.loads((HERE/'selection.json').read_text())['rows']
    selected=[r for r in rows if r['decision']=='SELECTED_CONDITIONAL']
    assert len(selected)==2
    wrappers={
      'Prob018_mux256to1':'module TopModule(input [255:0] in,input [7:0] sel,output out); RefModule reference_alias(.in(in),.sel(sel),.out(out)); endmodule\n',
      'Prob095_review2015_fsmshift':'module TopModule(input clk,input reset,output shift_ena); RefModule reference_alias(.clk(clk),.reset(reset),.shift_ena(shift_ena)); endmodule\n'}
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
    env['PATH']='D:/iverilog/bin'
    iv=Path('D:/iverilog/bin/iverilog.exe');vvp=Path('D:/iverilog/bin/vvp.exe')
    plan={'kind':'REFERENCE_ALIAS_ORIGINAL_HARNESS_SMOKE_ONLY','selected':[r['id'] for r in selected],
      'compile_cap':2,'simulation_cap':2,'compile_timeout':15,'simulation_timeout':10,
      'no_retries':True,'model_calls':0,'independence':False,
      'limits':'TopModule aliases same RefModule; tautological golden agreement, only harness/tool/receipt observation. No functional reference independence or mutation sensitivity claim.',
      'iverilog_sha256':sha(iv),'vvp_sha256':sha(vvp),'wrappers':wrappers,
      'selection_sha256':sha(HERE/'selection.json')}
    write(run/'plan.json',plan)
    results=[]
    for row in selected:
        folder=run/row['id'];folder.mkdir()
        for name,key in [('reference.sv','ref.sv'),('testbench.sv','test.sv')]:
            src=HERE/row['files'][key]['path'];assert sha(src)==row['files'][key]['sha256']
            (folder/name).write_bytes(src.read_bytes())
        (folder/'reference_alias.sv').write_bytes(wrappers[row['id']].encode())
        phases=[]
        for name,command,timeout in [
          ('compile',[str(iv),'-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o','sim.vvp','reference_alias.sv','testbench.sv','reference.sv'],15),
          ('simulate',[str(vvp),'sim.vvp'],10)]:
            start=time.monotonic()
            try:
                r=subprocess.run(command,cwd=folder,env=env,capture_output=True,timeout=timeout)
                stdout,stderr=r.stdout,r.stderr;rc=r.returncode;timedout=False
            except subprocess.TimeoutExpired as e:
                stdout,stderr=e.stdout or b'',e.stderr or b'';rc=None;timedout=True
            except OSError as e:
                stdout,stderr=b'',type(e).__name__.encode();rc=None;timedout=False
            (folder/(name+'.stdout.log')).write_bytes(stdout);(folder/(name+'.stderr.log')).write_bytes(stderr)
            phase=dict(stage=name,argv=command,timeout=timedout,returncode=rc,elapsed_seconds=time.monotonic()-start)
            phases.append(phase);write(folder/(name+'.json'),phase)
            if rc!=0 or timedout:break
        output=(folder/'simulate.stdout.log').read_text(encoding='utf-8',errors='replace') if (folder/'simulate.stdout.log').exists() else ''
        matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$',output,re.M)
        good=(len(phases)==2 and all(r['returncode']==0 and not r['timeout'] for r in phases)
              and len(matches)==1 and int(matches[0][0])==0 and int(matches[0][1])>0 and 'TIMEOUT' not in output)
        result=dict(task=row['id'],status='HARNESS_SMOKE_PASS' if good else 'CALIBRATION_FAILED_NO_RETRY',
            phases=phases,original_receipt=matches,model_candidate=False,reference_independence=False)
        results.append(result);write(run/'results.json',results)
        print(json.dumps({'task':row['id'],'status':result['status'],'receipt':matches}),flush=True)
        if not good:break
    write(run/'evidence-lock.json',{p.relative_to(run).as_posix():sha(p) for p in sorted(run.rglob('*')) if p.is_file()})
    return int(not all(r['status']=='HARNESS_SMOKE_PASS' for r in results) or len(results)!=len(selected))
if __name__=='__main__':raise SystemExit(main())
