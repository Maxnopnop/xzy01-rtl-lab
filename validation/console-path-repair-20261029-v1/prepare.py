from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
names=['console_bridge_v3.py','console_catalog_v3.py','console_gui_v3.py','console_cli_v3.py','console_school_v3.py','console_school_runner_v3.py','console_stage_v3.py','console_dependencies.json','Open-Lab-v3.cmd','Open-Lab-v3.ps1','test_console_multimodel.py','test_console_recovery_r1.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={n:sha(ROOT/n) for n in names}
for rel in ['exploration/20261028/public-rag-30-review-v1','exploration/20261029/main36-first-slot-incident-v1','validation/console-multimodel-20261024-v1','validation/console-v3-recovery-r1-20261028','validation/main36-path-review-20261029-v1']:
    for p in (ROOT/rel).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:protected[str(p.relative_to(ROOT))]=sha(p)
(HERE/'preservation-before.json').write_text(json.dumps(protected,indent=2),encoding='utf-8')
for sub in ('original','source'):
    d=HERE/sub;d.mkdir()
    for n in names[:10]:(d/n).write_bytes((ROOT/n).read_bytes())
d=HERE/'source'
p=d/'console_bridge_v3.py';s=p.read_text(encoding='utf-8')
s=s.replace("ROOT = Path(__file__).resolve().parent\nSTATE = ROOT / 'validation/console-multimodel-20261024-v1'", "CODE = Path(__file__).resolve().parent\nVERSION = CODE.parent\nROOT = VERSION.parents[1]\nSTATE = VERSION / 'w'\nLEGACY_STATES = (ROOT/'validation/console-openrouter-20261024-v1', ROOT/'validation/console-multimodel-20261024-v1')")
s=s.replace("RESULT_SCHEMA = 'console-result-v3-recovery-r1'","RESULT_SCHEMA = 'console-result-path-repair-v1'")
s=s.replace("return {n:sha(ROOT/n) for n in ('console_bridge_v3.py','console_catalog_v3.py','console_dependencies.json','console_gui_v3.py','console_cli_v3.py','console_school_v3.py','console_school_runner_v3.py','console_stage_v3.py')}","return {str((CODE/n).relative_to(ROOT)):sha(CODE/n) for n in ('console_bridge_v3.py','console_catalog_v3.py','console_paths.py','console_dependencies.json','console_gui_v3.py','console_cli_v3.py','console_school_v3.py','console_school_runner_v3.py','console_stage_v3.py')}")
s=s.replace("self.global_state = Path(state)\n        self.state = Path(state) / 'dispatch' / self.identity", "self.global_state = Path(state).resolve()\n        self.state = self.global_state / 'd' / self.identity[:16]")
s=s.replace("self.state/s['id']",'self.slot_dir(s)').replace('self.state/slot_id','self.slot_dir(slot_id)')
s=s.replace("self.global_state/'slot-reservations'/f'{slot_id}.json'","self.reservation_path(slot_id)")
s=s.replace("        self.verify()\n        release=read(release_path)","        self.verify()\n        self.check_release(release_path)\n        self.check_mapping()\n        self.check_legacy()\n        return self.check_ledger(slot_id)\n\n    def check_release(self,release_path):\n        release=read(release_path)")
s=s.replace("        require(not (ROOT/'validation/console-openrouter-20261024-v1/slot-reservations'/f'{slot_id}.json').exists(),'v2已有预约禁止重发')\n",'')
s=s.replace("        require(not (self.state/'STOP.json').exists()", "        require(release.get('work_root')==str(self.global_state),'放行须绑定固定短工作根目录')\n\n    def check_ledger(self,slot_id):\n        require(not (self.state/'STOP.json').exists()",1)
p.write_text(s,encoding='utf-8',newline='\n')
p=d/'console_cli_v3.py';s=p.read_text(encoding='utf-8').replace("b.ROOT/'console_cli_v3.py'","b.CODE/'console_cli_v3.py'");p.write_text(s,encoding='utf-8',newline='\n')
p=d/'console_school_v3.py';s=p.read_text(encoding='utf-8').replace("b.ROOT/'console_school_runner_v3.py'","b.CODE/'console_school_runner_v3.py'").replace("b.ROOT/'console_stage_v3.py'","b.CODE/'console_stage_v3.py'");p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'protected_files':len(protected),'source_copies':10,'model_calls':0}))
