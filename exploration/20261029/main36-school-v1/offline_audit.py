"""Package/transport tests only. No model or school tool calls."""
import ast,contextlib,hashlib,importlib.util,io,json,shutil,sys,zipfile
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[2];T=P/'offline';T.mkdir(exist_ok=False)
sys.path.insert(0,str(P/'reuse'));import console_stage_v3 as stage;import console_bridge_v3 as b;import console_school_v3 as school
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
records=read(P/'records.json');sources=read(P/'source-results-lock.json')
check('144 unique case/tool pairs',len(records)==144 and len({(r['ordinal'],r['tool']) for r in records})==144)
check('Original results/source hashes unchanged',all(sha(R/n)==h for n,h in sources.items()))
for item in records:
 rec=item['record'];archive=P/'outgoing'/rec['archive']
 check('%03d/%s archive'%(item['ordinal'],item['tool']),sha(archive)==rec['archive_sha256'])
 with contextlib.redirect_stdout(io.StringIO()):dest=stage.stage(archive,rec['archive_sha256'],home=T/'stage-home')
 m=read(dest/'console-manifest.json');src=R/'exploration/20261029/main36-proxy-newbatch-v1/live/jobs'/f"{item['ordinal']:03d}"
 check('%03d/%s exact DUT'%(item['ordinal'],item['tool']),(dest/'dut.sv').read_bytes()==(src/'dut.sv').read_bytes())
 if item['tool'] in ('vcs','xcelium'):
  check('%03d/%s exact TB/ref/count'%(item['ordinal'],item['tool']),all((dest/n).read_bytes()==(src/n).read_bytes() for n in ('testbench.sv','reference.sv')) and m['expected_checks']==item['expected_checks'])
 else:
  expected=P/'constraints'/('rule110.sdc' if item['task']=='Prob124_rule110' else 'comb.sdc')
  check('%03d/%s SDC mapping'%(item['ordinal'],item['tool']),(dest/'constraints.sdc').read_bytes()==expected.read_bytes())
for name in ('school_main.py','reuse/console_stage_v3.py','reuse/console_school_runner_v3.py','reuse/ece_synth_common.py','reuse/ece_synth_school.py'):
 ast.parse((P/name).read_text(encoding='utf-8'),feature_version=(3,6));check(name+' Python3.6 syntax',True)
first=records[0]['record'];f=T/'stage-home/xzy01-console-v3'/first['key']/'dut.sv';f.write_text('tampered')
try:stage.stage(P/'outgoing'/first['archive'],first['archive_sha256'],home=T/'stage-home');rejected=False
except ValueError:rejected=True
check('Existing changed HOME refused',rejected)
fakehome=T/'manual-home';base=fakehome/'xzy01-main36-school-v1';shutil.copytree(P/'outgoing',base)
(fakehome/'tsclient/FYP').mkdir(parents=True)
spec=importlib.util.spec_from_file_location('school_manual_fixture',base/'school_main.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
check('All bundle hashes and offline check',mod.checks(base,school=False)['status']=='READY_FOR_ONE_MANUAL_CASE')
check('All-case selection unavailable',len(mod.chosen(read(base/'index.json'),1,'vcs'))>0)
try:mod.chosen(read(base/'index.json'),0,'all');rejected=False
except ValueError:rejected=True
check('Invalid/all selection refused',rejected)
calls=[]
class Fake:
 def __init__(self,cmd):calls.append(cmd)
 def wait(self):return 0
 def poll(self):return 0
with patch.object(Path,'home',return_value=fakehome),patch.object(mod,'checks',return_value={'errors':[]}),patch.object(mod.subprocess,'Popen',Fake),patch.object(sys,'argv',['school_main.py','run','1','vcs']),contextlib.redirect_stdout(io.StringIO()):
 check('One manual call exits',mod.main()==0)
check('Exactly one selected tool, no next case',len(calls)==1 and 'run-one.sh' in calls[0][1])
(fakehome/'xzy01-console-single'/first['key']).mkdir(parents=True)
with patch.object(Path,'home',return_value=fakehome),patch.object(mod,'checks',return_value={'errors':[]}),patch.object(mod.subprocess,'Popen',Fake),patch.object(sys,'argv',['school_main.py','run','1','vcs']):
 try:mod.main();rejected=False
 except ValueError:rejected=True
check('Existing attempt refuses rerun',rejected and len(calls)==1)

# Synthetic return only: separate import state, never user shared folder.
b.STATE=T/'mock-import'
def mock_return(item,tamper=False):
 rec=item['record'];folder=Path(rec['local']);manifest=read(folder/'console-manifest.json')
 dest=T/('mock-return-'+item['tool']+('-tamper' if tamper else ''));dest.mkdir()
 payload={n:(folder/n).read_bytes() for n in manifest['inputs']};payload['console-manifest.json']=(folder/'console-manifest.json').read_bytes()
 result={'key':rec['key'],'manifest_sha256':rec['manifest_sha256'],'returncode':0}
 if item['tool']=='vcs':
  result.update(status='FIXED_TEST_PASS',samples=item['expected_checks'],mismatches=0)
  payload['simulate.log']=('Mismatches: 0 in %d samples\n'%item['expected_checks']).encode();payload['simulate.exit']=b'0\n'
 else:
  job=read(folder/'job.json');result['status']='COMPLETED_REVIEW_REQUIRED'
  payload['execution.json']=json.dumps({'returncode':0,'nonce':job['nonce']}).encode();payload['receipt.txt']=('XZY01_SYNTH_V1 '+job['nonce']+' COMPLETE').encode()
  for n in ('outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt'):payload[n]=b'OFFLINE_SYNTHETIC_ONLY'
 payload['console-result.json']=json.dumps(result).encode()
 if tamper:payload['dut.sv']=b'tampered'
 archive=dest/('return-'+rec['key']+'.zip')
 with zipfile.ZipFile(archive,'x') as z:
  for n,v in payload.items():z.writestr(n,v)
 side=archive.with_suffix('.json');side.write_text(json.dumps({'key':rec['key'],'manifest_sha256':rec['manifest_sha256'],'archive_sha256':sha(archive)}))
 return side
for tool in ('vcs','dc'):
 item=next(r for r in records if r['ordinal']==1 and r['tool']==tool)
 side=mock_return(item);got=school.collect(item['record'],side)
 check(tool+' mock return import',got['verified'] is True)
 check(tool+' identical return idempotent',school.collect(item['record'],side)==got)
 side=mock_return(item,True)
 try:school.collect(item['record'],side);rejected=False
 except ValueError:rejected=True
 check(tool+' changed DUT return rejected',rejected)
check('Original result evidence still unchanged',all(sha(R/n)==h for n,h in sources.items()))
out={'passed':True,'checks':checks,'check_count':len(checks),'packages':144,'real_model_calls':0,'real_eda_calls':0,'synthetic_returns_not_school_results':True}
with (P/'offline-audit.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'passed':True,'checks':len(checks),'real_eda_calls':0}))
