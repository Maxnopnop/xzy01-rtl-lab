"""Static original receipt parser; does not execute or modify upstream tests."""
import re
def classify(compile_rc,simulation_rc,output,timeout=False):
    if timeout:return 'TIMEOUT'
    if compile_rc is None:return 'NOT_RUN'
    if compile_rc!=0:return 'COMPILE_FAIL_UNCLASSIFIED'
    if simulation_rc is None:return 'NOT_RUN_SIMULATION'
    if 'TIMEOUT' in output:return 'TIMEOUT'
    if simulation_rc!=0:return 'SIM_ERROR'
    rows=re.findall(r'^Mismatches: (\d+) in (\d+) samples\s*$',output,re.M)
    if len(rows)!=1 or int(rows[0][1])<=0:return 'INVALID_ORIGINAL_RECEIPT'
    return 'ORIGINAL_PASS' if int(rows[0][0])==0 else 'ORIGINAL_FUNCTION_FAIL'
