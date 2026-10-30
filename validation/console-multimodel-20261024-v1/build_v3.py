"""One-time independent version construction. Never changes v2 or experimental packets."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
old=['console_bridge.py','console_gui_v2.py','console_cli.py','console_school.py','console_school_runner.py','console_dependencies.json','Open-Lab-v2.cmd','Open-Lab-v2.ps1']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/n for n in old]}
for folder in ['validation/console-openrouter-20261024-v1/delivery-final','validation/console-school-four-slot025-v1']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file():protected[str(p.relative_to(ROOT))]=sha(p)
(HERE/'preservation-before.json').write_text(json.dumps(protected,indent=2),encoding='utf-8')
def write(n,s):
    with (ROOT/n).open('x',encoding='utf-8',newline='\n') as f:f.write(s)
s=(ROOT/'console_bridge.py').read_text(encoding='utf-8')
s=s.replace("STATE = ROOT / 'validation/console-openrouter-20261024-v1'","STATE = ROOT / 'validation/console-multimodel-20261024-v1'")
s=s.replace("MODELS = tuple('openai/gpt-5.6-' + x for x in ('luna', 'terra', 'sol'))","# Model membership comes only from the frozen package.")
s=s.replace("('console_bridge.py','console_dependencies.json','console_gui_v2.py','console_cli.py','console_school.py','console_school_runner.py')","('console_bridge_v3.py','console_catalog_v3.py','console_dependencies.json','console_gui_v3.py','console_cli_v3.py','console_school_v3.py','console_school_runner_v3.py','console_stage_v3.py')")
s=s.replace("'console-frozen-v1'","'console-frozen-v3'").replace('需要 console-frozen-v1','需要 console-frozen-v3')
s=s.replace('        groups = {};task_inputs={}',"        from console_catalog_v3 import profiles\n        self.models=profiles(self)\n        groups = {};task_inputs={}")
s=s.replace("s['model'] in MODELS","s['model'] in self.models")
s=s.replace("            require(set(obj) <= {'model', 'messages', 'stream', 'provider', 'max_tokens', 'max_completion_tokens', 'temperature', 'seed', 'reasoning'}, '未知请求字段')\n            require(obj.get('provider') == {'only':['openai'], 'allow_fallbacks':False, 'require_parameters':True}, '必须固定 OpenAI provider 并禁止 fallback')", "            profile=self.models[s['model']]\n            require(set(obj)=={'model','messages','stream','provider'}|set(profile['parameters']), '请求字段不等于冻结模型参数')\n            require({k:obj[k] for k in profile['parameters']}==profile['parameters'],'模型参数值变化')\n            require(obj.get('provider') == {'only':[profile['provider_tag']], 'allow_fallbacks':False, 'require_parameters':True}, '端点路由不匹配或允许fallback')")
s=s.replace("            msg = canonical(messages)","            require(s['messages_file'] in lock and s['retrieved_file'] in lock,'完整消息或检索片段未冻结')\n            message_bytes=inside(self.base,s['messages_file']).read_bytes()\n            require(json.loads(message_bytes)==messages,'实际消息与冻结原消息不同')\n            msg = (message_bytes,inside(self.base,s['retrieved_file']).read_bytes())")
s=s.replace("        require(all(v == settings[0] for v in settings), '三模型采样/输出预算不一致')", "        # Differences are frozen per model and explicitly reviewed; never normalize them.")
s=s.replace('set(MODELS)','set(self.models)').replace('for model in MODELS','for model in self.models').replace('三模型样本机会不相同','声明模型集合样本机会不相同')
s=s.replace("        require(release.get('budget_policy')==self.data['budget_policy'], '放行预算口径不匹配')", "        require(release.get('budget_policy')==self.data['budget_policy'], '放行预算口径不匹配')\n        require(release.get('model_profiles_sha256')==digest(canonical(self.data['models'])) and release.get('model_comparison_reviewed') is True,'模型参数/路由差异尚未审核')\n        require(self.data.get('purpose')!='OFFLINE_FIXTURE','离线示例禁止真实放行')\n        require(not (ROOT/'validation/console-openrouter-20261024-v1/slot-reservations'/f'{slot_id}.json').exists(),'v2已有预约禁止重发')")
s=s.replace("provider_only=['openai'],expected_provider='OpenAI'","provider_only=[self.models[s['model']]['provider_tag']],expected_provider=self.models[s['model']]['response_provider']")
s=s.replace("body.get('provider')!='OpenAI'","body.get('provider')!=self.models[s['model']]['response_provider']")
s=s.replace("    require(body.get('model')==obj['model'] and body.get('provider')=='OpenAI','原响应模型身份不符')", "    if row['dataset'] in HISTORY:expected_provider='OpenAI'\n    else:\n        imported=Package(row['manifest_path'])\n        expected_provider=imported.models[obj['model']]['response_provider']\n    require(body.get('model')==obj['model'] and body.get('provider')==expected_provider,'原响应模型身份不符')")
write('console_bridge_v3.py',s)
for src,dest in [('console_cli.py','console_cli_v3.py'),('console_gui_v2.py','console_gui_v3.py'),('console_school.py','console_school_v3.py'),('console_school_runner.py','console_school_runner_v3.py'),('Open-Lab-v2.ps1','Open-Lab-v3.ps1'),('Open-Lab-v2.cmd','Open-Lab-v3.cmd')]:
    s=(ROOT/src).read_text(encoding='utf-8').replace('console_bridge as b','console_bridge_v3 as b').replace('console_school as school','console_school_v3 as school').replace('console_cli import','console_cli_v3 import').replace('console_cli.py','console_cli_v3.py').replace('console_gui_v2.py','console_gui_v3.py').replace('Open-Lab-v2.ps1','Open-Lab-v3.ps1').replace('console_school_runner.py','console_school_runner_v3.py').replace('控制台 v2','控制台 v3')
    write(dest,s)
