"""Versioned new release candidate; frozen root runner and v1 plan unchanged."""
import importlib.util,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(BASE))
spec=importlib.util.spec_from_file_location('r6_frozen_core',BASE/'runner.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
core.RUN=BASE/'runs/prepared-v2'
original_hashes=core.hashes
def hashes():
    d=original_hashes()
    for p in sorted((BASE/'engineering-v2').glob('*.py')):
        d[str(p.relative_to(core.ROOT))]=core.lab.digest(p.read_bytes())
    return d
core.hashes=hashes
original_prepare=core.prepare
def prepare():
    assert core.batch.read(BASE/'runs/recovery-job-binding-v2/summary.json')['status']=='PASS'
    original_prepare()
core.prepare=prepare
if __name__=='__main__':core.main()
