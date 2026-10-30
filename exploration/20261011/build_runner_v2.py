"""Create separate v2 files; never patch the frozen R3 source."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;OLD=HERE/'r3';NEW=HERE/'r3-runner-v2'
def main():
    NEW.mkdir(exist_ok=True);dest=NEW/'runner.py';assert not dest.exists()
    source=(OLD/'runner.py').read_text(encoding='utf-8')
    def replace(old,new):
        nonlocal source
        assert old in source,old
        source=source.replace(old,new)
    replace('R3 prepare-only by default','R3 runner v2, separate namespace and invalid-format retention; prepare-only by default')
    replace('sys.path[:0]=[str(BASE),str(ROOT)]','OLD=BASE.parent/"r3";sys.path[:0]=[str(BASE),str(OLD),str(ROOT)]')
    replace("RUN=BASE/'runs/prepared-v1';ASSETS=BASE/'assets-v1'","RUN=BASE/'runs/prepared-v2';ASSETS=OLD/'assets-v1'\nFUNCTIONAL_STATUSES=frozenset({'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED','EXTRACTION_ERROR'})")
    replace("[BASE/'R3_PROTOCOL.md']","[BASE/'PROTOCOL.md',OLD/'tasks.py']")
    replace("(BASE/'references').glob('*.sv')","(OLD/'references').glob('*.sv')")
    start=source.index('def freeze_assets():');end=source.index('def facts(task):')
    source=source[:start]+source[end:]
    replace("assert batch.read(BASE/'runs/calibration-v1/summary.json')['status']=='PASS'\n    assert batch.read(BASE/'runs/control-tests-v1/summary.json')['status']=='PASS'","assert batch.read(OLD/'runs/calibration-v1/summary.json')['status']=='PASS'\n    assert batch.read(BASE/'runs/acceptance-v1/summary.json')['status']=='PASS'")
    replace("kind='R3_SHARED_FIRST_RTL_PUBLIC_FEEDBACK'","kind='R3_RUNNER_V2_ENGINEERING_PREPARATION'")
    replace("stage='first'","role='first'");replace("stage='branch'","role='branch'")
    replace("job['stage']","job['role']");replace("r['stage']","r['role']")
    replace("if feedback['status'] not in ('PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED'):","if feedback['status'] not in FUNCTIONAL_STATUSES:")
    replace("row.update(batch.read(jf))","row['judge']=batch.read(jf)\n                row['status']=row['judge']['status']")
    replace("comparisons=[];valid={'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED'}","comparisons=[];valid=FUNCTIONAL_STATUSES")
    dest.write_bytes(source.encode('utf-8'));(NEW/'judge.py').write_bytes((OLD/'judge.py').read_bytes())
    (NEW/'derivation.json').write_text(json.dumps(dict(original_runner_sha256=hashlib.sha256((OLD/'runner.py').read_bytes()).hexdigest(),new_runner_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),judge_copy_sha256=hashlib.sha256((NEW/'judge.py').read_bytes()).hexdigest(),note='Independent new files; unchanged R3 tasks/assets/read-only dependencies'),indent=2),encoding='utf-8')
    print('Created',dest)
if __name__=='__main__':main()
