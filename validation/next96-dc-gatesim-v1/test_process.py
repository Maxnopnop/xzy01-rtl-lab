"""Offline synthetic subprocess checks, no school EDA tools."""
import sys,tempfile,json
from pathlib import Path
import school_sim as s
checks={}
with tempfile.TemporaryDirectory(prefix='next96-process-test-') as tmp:
    p=Path(tmp)
    ok=s.bounded([sys.executable,'-c','print("synthetic process")'],p,3)
    checks['normal_process']=ok['status']=='EXITED' and ok['returncode']==0
    slow=s.bounded([sys.executable,'-c','import time; time.sleep(10)'],p,.3)
    checks['timeout_killed']=slow['status']=='TIMEOUT' and slow['returncode']!=0 and slow['elapsed_seconds']<5
assert all(checks.values())
result=dict(checks=checks,synthetic_processes=2,model_calls=0,eda_calls=0)
s.save(Path(__file__).parent/'process-verification.json',result)
print(json.dumps(result))
