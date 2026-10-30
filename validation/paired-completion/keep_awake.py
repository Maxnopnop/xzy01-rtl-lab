import ctypes,json,time
from pathlib import Path
root=Path(__file__).resolve().parent
flag=ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
(root/'awake-status.json').write_text(json.dumps({'started_epoch':time.time(),'request_succeeded':bool(flag),'purpose':'Prevent idle sleep during bounded paired experiment; no permanent power setting changes'}))
try:
    end=time.monotonic()+7200
    while time.monotonic()<end and not (root/'release-awake').exists():time.sleep(10)
finally:
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
