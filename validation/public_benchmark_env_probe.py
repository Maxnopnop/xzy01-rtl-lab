"""Bounded compiler-environment diagnosis; no benchmark rerun or model call."""
import os, json, subprocess, hashlib
from pathlib import Path

out = Path(__file__).parent / 'public-benchmark-env-probe-20261016'
out.mkdir(exist_ok=False)
(out / 'probe.sv').write_text('module tb; initial $finish; endmodule\n', encoding='ascii')
base = {k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
base['PATH'] = 'D:/iverilog/bin'
comspec = str(Path(os.environ['SystemRoot'])/'System32'/'cmd.exe')
variants = [('original_minimal', base), ('add_comspec',dict(base, COMSPEC=comspec)),
            ('add_system32_path',dict(base, PATH='D:/iverilog/bin;'+str(Path(os.environ['SystemRoot'])/'System32'))),
            ('add_both',dict(base, COMSPEC=comspec, PATH='D:/iverilog/bin;'+str(Path(os.environ['SystemRoot'])/'System32')))]
rows=[]
for name, env in variants:
    argv=['D:/iverilog/bin/iverilog.exe','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o',name+'.vvp','probe.sv']
    try:
        r=subprocess.run(argv,cwd=out,env=env,capture_output=True,timeout=15)
        rc=r.returncode; stdout=r.stdout; stderr=r.stderr
    except subprocess.TimeoutExpired:
        rc=None; stdout=b''; stderr=b'TIMEOUT'
    (out/(name+'.stdout.log')).write_bytes(stdout)
    (out/(name+'.stderr.log')).write_bytes(stderr)
    rows.append(dict(name=name, argv=argv, returncode=rc, stdout_bytes=len(stdout),stderr_bytes=len(stderr),binary_exists=(out/(name+'.vvp')).exists()))
report={'model_calls':0,'benchmark_compiles':0,'probe_compiles':len(rows),'simulations':0,'compiler_sha256':hashlib.sha256(Path('D:/iverilog/bin/iverilog.exe').read_bytes()).hexdigest(),'rows':rows}
(out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
