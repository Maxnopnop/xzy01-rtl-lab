"""Exactly one fresh required regression, default environment untouched."""
import sys,subprocess,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import runner
run=BASE/'runs/regression-v1';assert not run.exists();run.mkdir(parents=True)
r=subprocess.run([sys.executable,'-m','unittest','-v','test_lab','test_batch','test_dev','test_fsm'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(run/'unittest.log').write_bytes(r.stdout)
text=r.stdout.decode(errors='replace');runner.batch.atomic(run/'summary.json',dict(status='PASS' if r.returncode==0 else 'REGRESSION_FAILED',exit_code=r.returncode,real_model_calls=0,environment='Unmodified default proxy; no isolation/retry',result_lines=[l for l in text.splitlines() if l.startswith(('Ran ','FAILED','OK'))]))
runner.seal(run);print('REGRESSION_RECORDED',r.returncode)
