"""Read saved logs only; correct CRLF parsing without rerunning or overwriting evidence."""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for old in read(P/'calibration/summary.json')['results']:
 f=P/'calibration'/old['task'];c=read(f/'compile.json');s=read(f/'simulate.json')
 assert old['compile_log_sha256']==sha(f/'compile.json') and old['simulate_log_sha256']==sha(f/'simulate.json')
 matches=[re.fullmatch(r'Mismatches: (\d+) in (\d+) samples',line) for line in s['stdout'].splitlines()]
 matches=[m for m in matches if m]
 valid=c['returncode']==s['returncode']==0 and not any(x.get(k) for x in (c,s) for k in ('timeout','output_limit')) and len(matches)==1 and 'TIMEOUT' not in s['stdout'].upper()
 errors,count=map(int,matches[0].groups()) if len(matches)==1 else (None,None)
 rows.append({'task':old['task'],'original_parser_status':old['status'],'parser_issue':'CRLF not normalized before regex dollar anchor','corrected_status':'REFERENCE_SELF_MATCH' if valid and errors==0 and count>0 else 'REFERENCE_FAILURE','expected_checks':count if valid and errors==0 and count>0 else None,'mismatches':errors,'compile_log_sha256':sha(f/'compile.json'),'simulate_log_sha256':sha(f/'simulate.json'),'original_result_sha256':sha(f/'result.json'),'rerun':False,'independent_oracle':False})
with (P/'calibration/receipt-audit.json').open('x',encoding='utf-8') as f:json.dump({'rows':rows,'parse_rule':'splitlines then exact fullmatch; one receipt; require zero exit/no timeout/no output_limit/positive checks/zero mismatches','new_compile':0,'new_simulate':0,'preserved_original_errors':True},f,indent=2)
print([(r['task'],r['corrected_status'],r['expected_checks']) for r in rows])
