"""Original VerilogEval receipt parsing; never equate exit0 with PASS."""
import re

def assess(stdout, phases):
 lines=stdout.splitlines()
 found=[re.fullmatch(r'Mismatches: (\d+) in (\d+) samples',s) for s in lines]
 found=[(int(m[1]),int(m[2])) for m in found if m]
 timeout_text=any('TIMEOUT' in s.upper() for s in lines)
 good=(len(phases)==2 and all(p['returncode']==0 and not p.get('limit_reason') and not p.get('launch_error') for p in phases) and len(found)==1 and found[0][0]==0 and found[0][1]>0 and not timeout_text)
 return {'status':'HARNESS_SMOKE_PASS' if good else 'CALIBRATION_FAILED_NO_RETRY','original_receipt':found,'timeout_text':timeout_text,'reference_independence':False,'model_score':False}
