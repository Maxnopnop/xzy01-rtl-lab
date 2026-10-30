"""Read-only coordinator verification of next96 inputs and local tool evidence."""
import hashlib,json,re,ast
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
EXE=LAB/'exploration/20261024/public-rag-next-executor-v1'
B=LAB/'exploration/20261024/public-rag-next-v1'
evidence={}
def raw(p):
    p=Path(p);b=p.read_bytes();evidence[str(p)]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def lock(p,base=None):
    d=read(p)
    for name,h in d.items():assert sha(base/name if base else Path(name))==h,name
    return len(d)
report={'utc':datetime.now(timezone.utc).isoformat(),'model_calls':0,'network_requests':0,'eda_calls':0}
report['source_files']=lock(EXE/'source-lock.json',EXE)
report['input_files']=lock(EXE/'input-lock.json')
report['tool_files']=lock(EXE/'tools-lock.json')
report['packet_files']=lock(B/'packet-lock.json',B)
slots=read(B/'C/slots.json');assert len(slots)==96
groups={}
for s in slots:
    assert s['status']=='NOT_STARTED' and s['reserved'] is False
    p=B/s['request'];assert sha(p)==s['request_sha256']
    obj=read(p);assert obj.pop('model')==s['wire_model']=='openai/'+s['model']
    assert set(obj)=={'messages','stream','provider'}
    key=s['task'],s['condition'],s['sample'];groups.setdefault(key,[]).append(obj)
assert len(groups)==32 and all(len(v)==3 and v[0]==v[1]==v[2] for v in groups.values())
report['identical_full_request_groups']=32
cal=read(EXE/'calibration/summary.json');assert cal['passed'] and cal['compile_attempts']==cal['sim_attempts']==8
lock(EXE/'calibration/evidence-lock.json',EXE/'calibration')
report['calibration']=[]
for row in cal['rows']:
    task=row['task'];folder=EXE/'calibration'/task
    ref=raw(B/'B/originals/dataset_spec-to-rtl'/f'{task}_ref.sv')
    test=raw(B/'B/originals/dataset_spec-to-rtl'/f'{task}_test.sv')
    assert raw(folder/'reference.sv')==ref and raw(folder/'testbench.sv')==test
    assert raw(folder/'dut.sv')==ref.replace(b'module RefModule',b'module TopModule',1)
    for phase in ('compile','simulate'):
        receipt=read(folder/(phase+'-receipt.json'))
        assert receipt['returncode']==0 and receipt['limit_reason'] is None and receipt['launch_error'] is None
        for channel in ('stdout','stderr'):assert sha(folder/f'{phase}.{channel}.bin')==receipt[channel+'_sha256']
    output=raw(folder/'simulate.stdout.bin').decode()
    matched=re.findall(r'^Mismatches: (\d+) in (\d+) samples$', '\n'.join(output.splitlines()), re.M)
    assert len(matched)==1 and int(matched[0][0])==0 and int(matched[0][1])>0
    report['calibration'].append({'task':task,'samples':int(matched[0][1]),'errors':0,'reference_alias_only':True})
# The controls-only revision after calibration must not alter judge/process/tools.
prior=read(EXE/'development/calibration-source-lock.json')
if prior:
    for name in ('core.py','transport.py','usage.py','tools-lock.json'):assert sha(EXE/name)==prior[name]
report['runtime_exists']=(EXE/'runtime/live-run').exists()
report['status']='STATIC_AND_CALIBRATION_PASS_MOCK_REVIEW_PENDING'
if (EXE/'mock/summary.json').exists():
    mock=read(EXE/'mock/summary.json')
    assert mock['passed'] and all(v is True for v in mock['checks'].values())
    assert mock['source_lock_sha256']==sha(EXE/'source-lock.json')
    assert mock['posts']==104 and mock['external_model_calls']==mock['eda_calls']==0
    captured=read(EXE/'mock/http-records.json')
    assert captured['counts']['success']==96 and sum(captured['counts'].values())==104
    assert all(r['synthetic_auth'] for r in captured['records'])
    for s in slots:
        assert raw(EXE/'mock/captures/success'/f'{s["ordinal"]:03d}.bin')==raw(B/s['request'])
        result=read(EXE/'mock/success/results'/f'{s["id"]}.json')
        assert result['mode']=='MOCK' and result['status']=='MOCK_ONLY_NOT_EDA'
        transport=read(EXE/'mock/success/jobs'/f'{s["ordinal"]:03d}'/'transport-response.json')
        assert transport['client_post_invocations']==1 and transport['request_sha256']==s['request_sha256']
    for case in read(EXE/'mock/failure-matrix.json'):
        assert case['passed'] and case['posts']==1 and case['remaining']==1
        mode=case['mode'];folder=EXE/'mock/failures'/mode
        assert len(list((folder/'reservations').glob('*.json')))==1
        assert (folder/'STOP.json').exists()
        transport=read(folder/'jobs/001/transport-response.json')
        assert transport['client_post_invocations']==1
    for scenario in ('pending','missing_STOP'):
        assert (EXE/'mock'/scenario/'STOP.json').exists()
        assert not list((EXE/'mock'/scenario/'jobs').rglob('request.json'))
    report.update(mock_posts=104,mock_checks=len(mock['checks']),failure_modes=8,
        mock_payloads_byte_exact=96,status='CALIBRATION_AND_MOCK_PASS_GATE_REVIEW_PENDING')
if (EXE/'gate-tests/summary.json').exists():
    gate=read(EXE/'gate-tests/summary.json')
    assert gate['passed']
    report['gate_tests']=gate
    report['status']='OFFLINE_TECHNICAL_CHECKS_PASS'
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'evidence-lock.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
