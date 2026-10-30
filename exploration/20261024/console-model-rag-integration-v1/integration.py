"""Versioned data validation facade; dispatch/replay/collection reuse the old console.
Private module instances prevent changing the old console's globals or source locks.
No network, key lookup, or EDA at import time.
"""
import collections
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

b = load('model_rag_private_bridge', 'console_bridge.py')
BasePackage = b.Package
b.STATE = HERE/'runtime'
MODELS = ('openai/gpt-4o-mini', 'openai/gpt-4.1-mini', 'openai/gpt-5.6-luna')
PROFILES = {m: ({'reasoning': {'effort': 'medium'}} if m.endswith('luna') else {}) for m in MODELS}

def bindings():
    return {p.name: b.sha(p) for p in (HERE/n for n in ('integration.py','console.py','home_transfer.py','home_one.py'))}

class Package(BasePackage):
    def __init__(self, manifest, state=None):
        super().__init__(manifest, b.STATE if state is None else state)

    def verify(self):
        d = self.data
        b.require(d.get('integration') == 'earlier-model-rag-v1', '不是本接入版本的数据包')
        b.require(d.get('models') == list(MODELS), '模型选择未冻结或与本版本不符')
        b.require(d.get('model_profiles') == PROFILES, '模型推理差异未按本版本冻结')
        b.require(b.sha(self.path) == self.identity, '清单发生变化')
        b.require(d.get('budget_policy') == 'calls_and_output_cap', '本版本需要显式输出上限')
        b.require(d.get('name') not in b.HISTORY, '新批次不能使用历史数据集名称')
        files=d['files'];groups={};inputs={};common=[]
        for n,h in files.items(): b.require(b.sha(b.inside(self.base,n))==h, '冻结输入变化: '+n)
        for s in self.slots:
            b.require(s['id'].startswith(d['name']+'-'), '槽位必须以独立数据集名称为前缀')
            b.safe_id(d['name'])
            b.require(s['model'] in MODELS and s['request'] in files, '模型或请求未冻结')
            obj=b.read(b.inside(self.base,s['request']))
            allowed={'model','messages','stream','provider','max_tokens','reasoning'}
            b.require(set(obj)<=allowed and obj.get('model')==s['model'] and obj.get('stream') is False, '请求字段不符')
            b.require(obj.get('provider')=={'only':['openai'],'allow_fallbacks':False,'require_parameters':True}, '路由不可变更')
            b.require(type(obj.get('max_tokens')) is int and 0<obj['max_tokens']<=16384, '输出上限须在共同支持范围')
            actual={k:obj[k] for k in ('reasoning',) if k in obj}
            b.require(actual==PROFILES[s['model']], '实际模型设置不符')
            common.append({k:v for k,v in obj.items() if k not in ('model','messages','reasoning')})
            msgs=obj['messages']
            b.require(isinstance(msgs,list) and msgs and all(set(m)=={'role','content'} and m['role'] in ('system','user') and isinstance(m['content'],str) for m in msgs), '只允许冻结 system/user')
            b.require(type(s['sample']) is int and s['sample']>0, '样本编号无效')
            g=groups.setdefault((s['task'],s['condition']), {'messages':b.canonical(msgs),'models':collections.Counter()})
            b.require(g['messages']==b.canonical(msgs), '同题同条件完整消息不一致')
            g['models'][s['model']]+=1
            for k in ('spec','testbench','reference'): b.require(s[k] in files, '原输入未冻结')
            b.require(not s.get('assets'), '本版本学校通路不支持额外 assets')
            b.require(b.re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',s.get('top','TopModule')), 'top 无效')
            b.require(type(s['expected_checks']) is int and s['expected_checks']>0, '校准检查数未冻结')
            inp={k:files[s[k]] for k in ('spec','testbench','reference')}
            inp.update(top=s.get('top','TopModule'),expected_checks=s['expected_checks'])
            b.require(inputs.setdefault(s['task'],inp)==inp,'同题测试/参考/规格发生变化')
        b.require(all(x==common[0] for x in common), '公共输出预算或路由不一致')
        for g in groups.values(): b.require(set(g['models'])==set(MODELS) and len(set(g['models'].values()))==1,'各模型机会不平衡')
        for task in inputs:
            arms={s['condition'] for s in self.slots if s['task']==task}
            b.require(arms=={'rag','no_rag'},'必须有两条件')
            samples=[sorted(s['sample'] for s in self.slots if s['task']==task and s['condition']==a and s['model']==m) for a in sorted(arms) for m in MODELS]
            b.require(all(x==samples[0] and len(x)==len(set(x)) for x in samples),'两条件样本不平衡')
            # Freeze the exact additive transformation, not merely equal hashes across models.
            nr=json.loads(groups[(task,'no_rag')]['messages']); rr=json.loads(groups[(task,'rag')]['messages'])
            context=d['contexts'][task]
            b.require(context in files,'RAG 实际上下文未冻结')
            suffix=b.inside(self.base,context).read_bytes().decode('utf-8')
            b.require(bool(suffix) and nr[-1]['role']=='user','缺 RAG 上下文或最后 user 消息')
            expected=[dict(m) for m in nr];expected[-1]['content']+=suffix
            b.require(rr==expected,'有无 RAG 必须仅差冻结的追加参考内容')
        b.require(d['max_calls']==len(self.slots),'机会预算与清单不符')

    def gate(self, release_path, slot_id):
        b.require(self.data.get('execution_status')=='READY_FOR_REVIEW','准备材料/夹具不允许正式执行')
        release=b.read(release_path)
        b.require(release.get('integration_sources')==bindings(),'接入源码放行绑定失效')
        # A dollar bound is mandatory; absence/unknown accounting never permits continuation.
        cap=self.data.get('max_cost_usd')
        b.require(type(cap) in (int,float) and math.isfinite(cap) and cap>0,'费用上限未确定')
        b.require(release.get('max_cost_usd')==cap,'费用放行与冻结不符')
        bounds=self.data.get('slot_cost_bounds_usd',{})
        b.require(set(bounds)=={s['id'] for s in self.slots} and all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in bounds.values()),'各槽保守费用界未冻结')
        b.require(sum(bounds.values())<=cap,'总费用界超过上限')
        spent=0
        for s in self.slots:
            result=self.state/s['id']/'result.json'
            if result.exists():
                cost=b.read(result).get('cost')
                b.require(type(cost) in (int,float) and math.isfinite(cost) and cost>=0,'存在未知费用，先核账')
                b.require(cost<=bounds[s['id']], '实际费用超出冻结估计，停止')
                spent+=cost
        b.require(slot_id in bounds and spent+bounds[slot_id]<=cap,'剩余费用上限不足')
        return super().gate(release_path,slot_id)

# These assignments affect only these isolated instances, not console_bridge imported by v2.
b.Package=Package
school=load('model_rag_private_school','console_school.py')
school.b=b
gui=load('model_rag_private_gui','console_gui_v2.py')
gui.b=b;gui.school=school
