"""Required offline regression for meaningful new runner/transport change."""
from pathlib import Path
import subprocess,sys,json,re
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];RUN=BASE/'r3-runner-v3/runs/regression-v1'
assert not RUN.exists();RUN.mkdir(parents=True)
with (RUN/'unittest.log').open('wb') as log:
    result=subprocess.run([sys.executable,'-m','unittest','-v','test_lab','test_batch','test_dev','test_fsm'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=180)
text=(RUN/'unittest.log').read_text(encoding='utf-8',errors='replace')
summary=dict(status='PASS' if result.returncode==0 else 'REGRESSION_FAILED',exit_code=result.returncode,real_model_calls=0,environment='Unmodified default proxy; no loopback isolation',ran=re.findall(r'Ran \d+ tests[^\n]*',text),result_lines=re.findall(r'(?:FAILED|OK)[^\n]*',text))
(RUN/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
