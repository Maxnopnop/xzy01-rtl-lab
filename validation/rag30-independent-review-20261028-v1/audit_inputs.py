"""Independent read-only audit. Does not import target code or run any tools/network."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P=ROOT/'exploration/20261028/public-rag-30-review-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    checked=[]
    scope=read(P/'scope.json');seal=read(P/'scope-seal.json')
    assert sha(P/'scope.json')==seal['scope_sha256']=='206b6ccf50c1665972d4b1e4c52c582902bb1a82a0616b3daf6fe2558b900e53'
    tasks=[r['id'] for r in scope['tasks']]
    assert len(tasks)==len(set(tasks))==30
    locks=read(P/'preservation-before.json')
    for name,h in locks.items():assert sha(ROOT/name)==h,name
    alock=read(P/'prior/A-lock.json')
    for name,h in alock.items():assert sha(P/'A'/name)==h,name
    assert len(alock)==14
    acq=read(P/'acquisition.json')
    assert len(acq)==90
    scope_files={(t['id'],k):v for t in scope['tasks'] for k,v in t['files'].items()}
    for r in acq:
        raw=(P/r['local']).read_bytes(); meta=scope_files[(r['task'],r['kind'])]
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert blob==r['expected_git_blob']==r['actual_git_blob']==meta['git_blob_sha1']
        assert hashlib.sha256(raw).hexdigest()==r['sha256'] and len(raw)==r['bytes']
        assert r['status']=='SAVED' and r['retries']==0
        assert r['utc']>seal['utc'] and scope['commit'] in r['url']
    assert sum(r['source']=='LOCAL_CACHE' for r in acq)==60
    summary=read(P/'calibration/summary.json'); amended=read(P/'calibration/receipt-audit.json')
    assert len(summary['results'])==len(amended['rows'])==30
    for old,new,task in zip(summary['results'],amended['rows'],tasks):
        assert old['task']==new['task']==task
        f=P/'calibration'/task; source=P/'originals/dataset_spec-to-rtl'
        ref=(source/(task+'_ref.sv')).read_bytes(); tb=(source/(task+'_test.sv')).read_bytes()
        assert (f/'reference.sv').read_bytes()==ref and (f/'testbench.sv').read_bytes()==tb
        alias,n=re.subn(rb'\bmodule\s+RefModule\b',b'module TopModule',ref,count=1)
        assert n==1 and (f/'dut.sv').read_bytes()==alias
        reserve=read(f/'reservation.json'); c=read(f/'compile.json');s=read(f/'simulate.json')
        assert reserve['retry']==0 and reserve['compile_attempt']==1
        assert reserve['reference_sha256']==hashlib.sha256(ref).hexdigest()
        assert reserve['testbench_sha256']==hashlib.sha256(tb).hexdigest()
        assert reserve['alias_sha256']==hashlib.sha256(alias).hexdigest()
        assert c['returncode']==s['returncode']==0
        assert not any(x.get(k) for x in (c,s) for k in ('timeout','output_limit','killed'))
        for n1 in ['compile','simulate']:
            assert old[n1+'_log_sha256']==new[n1+'_log_sha256']==sha(f/(n1+'.json'))
        matches=[m for line in s['stdout'].splitlines() if (m:=re.fullmatch(r'Mismatches: (\d+) in (\d+) samples',line))]
        assert len(matches)==1
        errors,count=map(int,matches[0].groups())
        assert errors==0 and count>0 and 'TIMEOUT' not in s['stdout'].upper()
        assert new['corrected_status']=='REFERENCE_SELF_MATCH' and new['expected_checks']==count
        assert new['original_result_sha256']==sha(f/'result.json') and new['rerun'] is False
        assert old['compile_attempts']==old['simulate_attempts']==1
        checked.append({'task':task,'checks':count,'mismatches':errors,'original_status':old['status'],'independent_oracle':False})
    evidence={str(q.relative_to(P)).replace('\\','/'):sha(q) for q in P.rglob('*') if q.is_file() and (q.is_relative_to(P/'originals') or q.is_relative_to(P/'A') or q.is_relative_to(P/'calibration') or q.name in ('scope.json','scope-seal.json','acquisition.json'))}
    result={'utc':datetime.now(timezone.utc).isoformat(),'passed':True,'preserved_prior_files':len(locks),'A_files':14,'original_git_blobs':90,'reference_compile_receipts':30,'reference_simulate_receipts':30,'reference_outcomes':checked,'new_compile_calls':0,'new_simulation_calls':0,'model_calls':0,'network_calls':0,'claim':'Only tool pipeline calibration/self-comparison; not independent oracle validation or model results','evidence_sha256':evidence}
    (HERE/'input-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='evidence_sha256'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
