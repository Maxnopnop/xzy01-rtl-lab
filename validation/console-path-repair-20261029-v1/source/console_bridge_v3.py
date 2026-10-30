"""Independent console bridge. Imports are read-only; dispatch is explicit and gated."""
import ast
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
import console_paths as paths

class DispatchFailure(ValueError):
    def __init__(self,diagnostic):
        self.diagnostic=diagnostic
        super().__init__('操作停止；'+diagnostic['stage']+'；未自动重试')

CODE = Path(__file__).resolve().parent
VERSION = CODE.parent
ROOT = VERSION.parents[1]
STATE = VERSION / 'w'
LEGACY_STATES = (ROOT/'validation/console-openrouter-20261024-v1', ROOT/'validation/console-multimodel-20261024-v1')
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
RESULT_SCHEMA = 'console-result-path-repair-v1'
# Model membership comes only from the frozen package.
ADAPTER = ROOT / 'exploration/20261024/public-rag-next-executor-v1'
TRANSPORT_SHA = '7ba1d3b47e2e471a9f11d226c65700d3cd70535b581fe7863a4fa4ed27c98524'
HISTORY = {
    'new96': ('exploration/20261024/public-rag-next-v1', 'exploration/20261024/public-rag-next-executor-v1'),
    'old240': ('exploration/20261023/public-rag-all20-v1', 'exploration/20261023/direct-api-v1'),
}

def read(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def sha(path):
    return digest(Path(path).read_bytes())

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())

def require(ok, message):
    if not ok:
        raise ValueError(message)

def inside(root, name):
    p = (Path(root) / name).resolve()
    require(p.is_relative_to(Path(root).resolve()), '路径超出实验包')
    return p

def safe_id(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}', value) and '..' not in value and not value.endswith('.'), '槽位 ID 不安全')
    return value

def bridge_bindings():
    return {str((CODE/n).relative_to(ROOT)):sha(CODE/n) for n in ('console_bridge_v3.py','console_catalog_v3.py','console_paths.py','console_dependencies.json','console_gui_v3.py','console_cli_v3.py','console_school_v3.py','console_school_runner_v3.py','console_stage_v3.py')}

def transport():
    path = ADAPTER / 'transport.py'
    require(sha(path) == TRANSPORT_SHA, '已审 transport 源码发生变化')
    spec = importlib.util.spec_from_file_location('console_audited_transport', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def historical_rows(name):
    batch_rel, exe_rel = HISTORY[name]
    batch, runtime = ROOT / batch_rel, ROOT / exe_rel / 'runtime/live-run'
    slots = read(batch / ('C/slots.json' if name=='new96' else 'slots.json'))
    rows = []
    for s in slots:
        result = runtime / 'results' / (safe_id(s['id']) + '.json')
        r = read(result) if result.exists() else {}
        job = runtime / 'jobs' / ('%03d' % s['ordinal'])
        req = job/'request.json' if (job/'request.json').exists() else inside(batch, s['request'])
        raw = req.read_bytes()
        expected=r.get('request_sha256',s['request_sha256'])
        require(digest(raw) == expected, '历史请求 hash 不匹配')
        obj = json.loads(raw)
        synth = ROOT / 'validation/next96-synthesis-v1/jobs' / ('%03d' % s['ordinal']) / 'result.json'
        synthesis = read(synth).get('synthesis_status') if name == 'new96' and synth.exists() else 'NOT_VERIFIED'
        rows.append(dict(s, dataset=name, status=r.get('status', 'UNKNOWN' if (runtime/'reservations'/result.name).exists() else 'NOT_STARTED'),
            messages_actual_sha256=digest(canonical(obj['messages'])), output_budget=obj.get('max_tokens', obj.get('max_completion_tokens')),
            result_path=str(result), job_dir=str(job), request_path=str(req), usage=r.get('usage'),
            cost=r.get('usage', {}).get('cost') if isinstance(r.get('usage'), dict) else None,
            receipt=r.get('receipt'), fixed_test=r.get('status','NOT_RUN'), synthesis=synthesis, actual_request_sha256=expected,
            response_model=r.get('response_model'),reported_provider=r.get('reported_provider'),read_only=True))
    return rows

def history():
    return [r for name in HISTORY for r in historical_rows(name)]

class Package:
    """Data-only package. Release is a separate coordinator artifact, never created here."""
    def __init__(self, manifest, state=STATE):
        self.path = Path(manifest).resolve()
        self.base = self.path.parent
        self.data = read(self.path)
        self.identity = sha(self.path)
        self.global_state = Path(state).resolve()
        self.state = self.global_state / 'd' / self.identity[:16]
        require(self.data.get('schema') == 'console-frozen-v3', '需要 console-frozen-v3 数据清单；不执行导入包中的脚本')
        self.slots = self.data['slots']
        require(0 < len(self.slots) <= 10000, '槽位数量无效')
        require(len({safe_id(s['id']) for s in self.slots}) == len(self.slots), '槽位重复')
        require([s['ordinal'] for s in self.slots]==list(range(1,len(self.slots)+1)), '冻结顺序不连续')
        self.verify()

    def slot_dir(self,slot):
        if isinstance(slot,str):slot=next(s for s in self.slots if s['id']==slot)
        return self.state/('%05d'%slot['ordinal'])

    def reservation_path(self,slot_id):
        return self.global_state/'r'/(digest(slot_id.encode())+'.json')

    def recovery_path(self,slot):
        return self.global_state/'e'/(digest(canonical([self.identity,slot['id']]))+'.json')

    def mapping(self):
        return dict(schema='console-short-map-v1',manifest_sha256=self.identity,work_root=str(self.global_state),slots=[dict(id=s['id'],ordinal=s['ordinal'],directory=self.slot_dir(s).name,request_sha256=self.data['files'][s['request']]) for s in self.slots])

    def check_mapping(self):
        if self.state.exists():require(read(self.state/'identity.json')==self.mapping(),'短路径映射缺失/身份冲突，禁止覆盖')

    def ensure_mapping(self):
        if self.state.exists():self.check_mapping();return
        self.state.mkdir(parents=True,exist_ok=False)
        save(self.state/'identity.json',self.mapping())

    def check_legacy(self):
        # No migration or continuation override: any previously reserved opportunity
        # blocks this package, even when its manifest hash or work root is changed.
        for old in LEGACY_STATES:
            require(not (old/'dispatch'/self.identity).exists(),'原批已有执行记录；仅允许另行审核接续，不迁移或重发')
            for s in self.slots:
                require(not (old/'slot-reservations'/(s['id']+'.json')).exists(),'原槽已预约；禁止换包绕过UNKNOWN或STOP')

    def verify(self):
        require(sha(self.path) == self.identity, '导入后清单发生变化')
        lock = self.data['files']
        for name, expected in lock.items():
            require(sha(inside(self.base, name)) == expected, '冻结输入变化: ' + name)
        from console_catalog_v3 import profiles
        self.models=profiles(self)
        groups = {};task_inputs={}
        settings = []
        for s in self.slots:
            require(s['request'] in lock, '请求未冻结')
            require(s['model'] in self.models, '不支持的模型；不允许替换')
            raw = inside(self.base, s['request']).read_bytes()
            obj = json.loads(raw)
            require(obj.get('model') == s['model'] and obj.get('stream') is False, '模型或 stream 不匹配')
            profile=self.models[s['model']]
            require(set(obj)=={'model','messages','stream','provider'}|set(profile['parameters']), '请求字段不等于冻结模型参数')
            require({k:obj[k] for k in profile['parameters']}==profile['parameters'],'模型参数值变化')
            require(obj.get('provider') == {'only':[profile['provider_tag']], 'allow_fallbacks':False, 'require_parameters':True}, '端点路由不匹配或允许fallback')
            cap = obj.get('max_tokens', obj.get('max_completion_tokens'))
            policy=self.data.get('budget_policy')
            require(policy in ('calls_only','calls_and_output_cap'), '须声明经审核的 budget_policy')
            require(not ('max_tokens' in obj and 'max_completion_tokens' in obj), '重复输出预算字段')
            if policy=='calls_only':require('max_tokens' not in obj and 'max_completion_tokens' not in obj, '按调用数预算不得额外注入 token 上限')
            else:require(type(cap) is int and cap>0, '冻结输出上限无效')
            messages = obj['messages']
            require(isinstance(messages, list) and messages and all(set(m)=={'role','content'} and m['role'] in ('system','user') and isinstance(m['content'],str) for m in messages), '只允许冻结 system/user 内容')
            key = (s['task'], s['condition'])
            require(s['messages_file'] in lock and s['retrieved_file'] in lock,'完整消息或检索片段未冻结')
            message_bytes=inside(self.base,s['messages_file']).read_bytes()
            require(json.loads(message_bytes)==messages,'实际消息与冻结原消息不同')
            msg = (message_bytes,inside(self.base,s['retrieved_file']).read_bytes())
            g = groups.setdefault(key, {'messages':msg, 'models':collections.Counter()})
            require(g['messages'] == msg, '同题同条件实际 messages 不一致')
            g['models'][s['model']] += 1
            settings.append({k:v for k,v in obj.items() if k not in ('model','messages')})
            for name in ('testbench', 'reference', 'spec'):
                require(s[name] in lock, '原输入未冻结: '+name)
            for name in s.get('assets', []):
                require(name in lock, '附加向量未冻结')
            require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',s.get('top','TopModule')), 'top 无效')
            require(type(s['expected_checks']) is int and s['expected_checks'] > 0, '固定检查数无效')
            inputs={key:lock[s[key]] for key in ('testbench','reference','spec')}
            inputs.update(assets={name:lock[name] for name in s.get('assets',[])},top=s.get('top','TopModule'),expected_checks=s['expected_checks'])
            require(task_inputs.setdefault(s['task'],inputs)==inputs,'同题原输入/测试/参考在模型或条件间发生变化')
        # Differences are frozen per model and explicitly reviewed; never normalize them.
        for g in groups.values():
            require(set(g['models']) == set(self.models) and len(set(g['models'].values()))==1, '声明模型集合样本机会不相同')
        for task in {s['task'] for s in self.slots}:
            arms={s['condition'] for s in self.slots if s['task']==task}
            require(arms=={'no_rag','rag'}, '本协议必须包含同题有/无RAG两臂')
            samples=[sorted(s['sample'] for s in self.slots if s['task']==task and s['condition']==arm and s['model']==model) for arm in sorted(arms) for model in self.models]
            require(all(x==samples[0] and len(set(x))==len(x) for x in samples),'两臂各模型样本数/编号不平衡')
        require(self.data['max_calls'] == len(self.slots), '调用上限必须绑定全部冻结槽位')

    def rows(self):
        rows=[]
        for s in self.slots:
            out=self.slot_dir(s)
            try:
                r=read(out/'result.json') if (out/'result.json').exists() else {}
                if not isinstance(r,dict):raise ValueError('Invalid result')
            except (ValueError,OSError):r={'status':'UNKNOWN','storage_error':True}
            occupied=out.exists() or self.reservation_path(s['id']).exists()
            legacy_occupied=any((old/'slot-reservations'/(s['id']+'.json')).exists() for old in LEGACY_STATES)
            if legacy_occupied and not r:r={'status':'UNKNOWN','legacy_reservation':True}
            local=r.get('local') if isinstance(r.get('local'),dict) else {}
            obj=read(inside(self.base,s['request']))
            rows.append(dict(s, dataset=self.data.get('name','imported'), status=r.get('status','UNKNOWN' if occupied else 'NOT_STARTED'),
                messages_actual_sha256=digest(canonical(obj['messages'])), output_budget=obj.get('max_tokens',obj.get('max_completion_tokens')),
                usage=r.get('usage'), cost=r.get('cost'), fixed_test=local.get('fixed_test','NOT_RUN'), synthesis=local.get('synthesis','NOT_RUN'), job_dir=str(out), result_path=str(out/'result.json'), manifest_path=str(self.path),manifest_sha256=self.identity,read_only=False))
            rows[-1].update(stopped=(self.state/'STOP.json').exists() or legacy_occupied or r.get('status')=='UNKNOWN',failure_stage=r.get('stage'),send_attempted=r.get('send_attempted'),recovery=r.get('recovery'),storage_error=r.get('storage_error',False))
            rows[-1].update(model_profile=self.models[s['model']],response_model=r.get('response_model'),reported_provider=r.get('reported_provider'),usage_note='原始usage保留；缺值为None，token/cache/reasoning口径及服务默认值可能不同，未自动折算')
        return rows

    def gate(self, release_path, slot_id):
        self.verify()
        self.check_release(release_path)
        self.check_mapping()
        self.check_legacy()
        return self.check_ledger(slot_id)

    def check_release(self,release_path):
        release=read(release_path)
        require(release.get('decision')=='CONSOLE_EXECUTION_RELEASE' and release.get('user_approved') is True, '批次未放行')
        require(release.get('owner')=='exploration' and release.get('reviewer_thread_id')=='01a12088-049c-7f32-8167-48be03bcc145', '须由探索负责、总控审核')
        require(release.get('manifest_sha256')==self.identity and release.get('bridge_sha256')==sha(__file__) and release.get('transport_sha256')==TRANSPORT_SHA, '放行绑定失效')
        require(release.get('source_hashes')==bridge_bindings(), '控制台完整源码绑定失效')
        for name,h in read(ROOT/'console_dependencies.json').items():
            require(sha(ROOT/name)==h,'冻结复用模块变化: '+name)
        require(release.get('max_calls')==self.data['max_calls'] and release.get('permitted_slots')==[s['id'] for s in self.slots], '放行额度或槽位不匹配')
        require(release.get('budget_policy')==self.data['budget_policy'], '放行预算口径不匹配')
        require(release.get('model_profiles_sha256')==digest(canonical(self.data['models'])) and release.get('model_comparison_reviewed') is True,'模型参数/路由差异尚未审核')
        require(self.data.get('purpose')!='OFFLINE_FIXTURE','离线示例禁止真实放行')
        require(release.get('automatic_retries')==0 and release.get('request_timeout_seconds')==180, '调用策略不匹配')
        require(release.get('work_root')==str(self.global_state),'放行须绑定固定短工作根目录')

    def check_ledger(self,slot_id):
        require(not (self.state/'STOP.json').exists(), '批次已停止，禁止继续或重发')
        slot=next((s for s in self.slots if s['id']==slot_id),None)
        require(slot is not None, '无此槽位')
        require(not (self.slot_dir(slot_id)).exists(), '已完成、失败或 unknown 槽不能重发')
        require(not (self.reservation_path(slot_id)).exists(), '此槽已在控制台预留，禁止换包重发')
        pending=[s for s in self.slots if not (self.slot_dir(s)).exists()]
        require(pending and pending[0]['id']==slot_id, '必须执行冻结顺序中的下一个未预约槽')
        # Package reuse cannot re-issue already reserved historical opportunities.
        for _, exe in HISTORY.values():
            require(not (ROOT/exe/'runtime/live-run/reservations'/f'{slot_id}.json').exists(), '历史槽已预留，禁止重发')
        require(sum((self.slot_dir(s)).exists() for s in self.slots)<self.data['max_calls'], '调用额度已用完')
        for s in self.slots:
            p=self.slot_dir(s)
            if p.exists():
                require(self.prior_allows_continue(s,p), '既有结果失败、缺损或未知；即使无STOP也禁止后续调用')
        return slot

    def prior_allows_continue(self, slot, folder):
        """Fail closed from durable results, including a crash before STOP is saved.

        STOP is a convenient marker, not the source of truth. Only the current
        result schema and known completed non-infrastructure outcomes may proceed.
        This read-only check never repairs a ledger or retries a reserved slot.
        """
        try:
            result=read(folder/'result.json')
            if not isinstance(result,dict) or result.get('schema')!=RESULT_SCHEMA:return False
            if result.get('status')!='GENERATED_UNVERIFIED':return False
            if result.get('request_sha256')!=self.data['files'][slot['request']]:return False
            if result.get('requested_model')!=slot['model'] or result.get('response_model')!=slot['model']:return False
            if result.get('reported_provider')!=self.models[slot['model']]['response_provider']:return False
            if result.get('rtl_sha256')!=sha(folder/'dut.sv'):return False
            local=result.get('local')
            if not isinstance(local,dict) or local.get('infrastructure_stop') is not False:return False
            if local.get('fixed_test') not in ('FIXED_TEST_PASS','FUNCTION_FAIL','COMPILE_ERROR','CHECK_COUNT_DIFFERENT'):return False
            if local.get('synthesis') not in ('SYNTH_PASS','SYNTH_FAIL'):return False
            return True
        except (OSError,ValueError,TypeError,KeyError):
            return False

    def dispatch(self, release_path, slot_id, secret):
        require(bool(secret), '请在隐藏输入框填写密钥')
        self.global_state.mkdir(parents=True,exist_ok=True)
        lock=self.global_state/'exclusive.lock'
        with lock.open('x') as f:
            f.write(str(os.getpid()))
        folder=None;result={};env=None;sent=False;stage='gate';slot=None
        try:
            s=self.gate(release_path,slot_id)
            slot=s
            raw=inside(self.base,s['request']).read_bytes()
            require(secret.encode() not in raw, '密钥不应出现在冻结请求里')
            result={'schema':RESULT_SCHEMA,'status':'UNKNOWN','usage':None,'cost':None,'request_sha256':digest(raw)}
            stage='identity_mapping';self.ensure_mapping()
            adapter=transport()
            cfg=dict(endpoint=ENDPOINT,api_key_env='OPENROUTER_API_KEY',proxy_url=self.data.get('proxy_url'),proxy_env=None,provider_only=[self.models[s['model']]['provider_tag']],expected_provider=self.models[s['model']]['response_provider'])
            route=adapter.route_values(cfg,{})
            folder=self.slot_dir(slot_id)
            folder.mkdir(exist_ok=False) # irreversible reservation before POST
            stage='path_preflight'
            paths.preflight(folder,[self.reservation_path(slot_id),self.recovery_path(s),self.state/'STOP.json'],s.get('assets',[]))
            stage='reservation'
            save(self.reservation_path(slot_id),{'slot_id':slot_id,'manifest_sha256':self.identity,'request_sha256':digest(raw),'work_root':str(self.global_state)})
            save(folder/'reservation.json',{'request_sha256':digest(raw),'manifest_sha256':self.identity,'status':'RESERVED_BEFORE_SEND'})
            stage='request_persist'
            (folder/'request.json').write_bytes(raw)
            save(folder/'attempt.json',{'slot_id':slot_id,'request_sha256':digest(raw),'manifest_sha256':self.identity,'stage':'BEFORE_SINGLE_POST','recovery_path':str(self.recovery_path(s))})
            stage='send_once';sent=True
            env=adapter.send_once(raw,route,secret,180)
            # Audited transport suppresses secret echoes; also protect mocked adapters.
            stage='response_validate_secret'
            require(secret not in json.dumps(env,ensure_ascii=False), '服务响应包含密钥，拒绝保存')
            stage='response_persist'
            save(folder/'transport-response.json',env)
            stage='response_identity'
            require(env.get('request_sha256')==digest(raw),'响应信封请求身份不符')
            if env.get('outcome')=='HTTP_OK':require(env.get('client_post_invocations')==1,'单POST回执不符')
            result={'schema':RESULT_SCHEMA,'status':env.get('outcome','UNKNOWN'),'usage':None,'cost':None,'request_sha256':digest(raw)}
            if env.get('outcome')=='HTTP_OK':
                stage='response_protocol'
                body=json.loads(env['body'])
                result.update(usage=body.get('usage'),cost=body.get('usage',{}).get('cost') if isinstance(body.get('usage'),dict) else None,
                    requested_model=s['model'],response_model=body.get('model'),reported_provider=body.get('provider'))
                result.update(requested_provider_tag=self.models[s['model']]['provider_tag'],route_evidence='Response provider name checked; exact backend endpoint tag is not exposed by standard response',usage_comparability='Raw provider usage; missing values remain null; tokenization/cache/reasoning/defaults are not normalized')
                if body.get('model')!=s['model'] or body.get('provider')!=self.models[s['model']]['response_provider']:
                    result['status']='MODEL_OR_PROVIDER_MISMATCH'
                    save(folder/'result.json',result)
                    save(self.state/'STOP.json',{'reason':result['status']})
                    return result
                choices=body['choices']
                require(len(choices)==1 and choices[0].get('finish_reason')=='stop', '响应未完整结束')
                message=choices[0]['message']
                require(message.get('role')=='assistant' and not message.get('tool_calls') and not message.get('function_call'), '不允许工具调用')
                text=message['content']
                require(isinstance(text,str) and len(text.encode())<=131072, 'RTL 响应大小无效')
                stage='model_output_persist'
                (folder/'model-output.txt').write_text(text,encoding='utf-8',newline='')
                try:
                    stage='rtl_extract_and_persist'
                    rtl=extract(text,s.get('top','TopModule'))
                    (folder/'dut.sv').write_text(rtl,encoding='utf-8',newline='')
                    result.update(status='GENERATED_UNVERIFIED',rtl_sha256=sha(folder/'dut.sv'))
                    for key,name in [('testbench','testbench.sv'),('reference','reference.sv')]:
                        (folder/name).write_bytes(inside(self.base,s[key]).read_bytes())
                    for asset in s.get('assets',[]):
                        target=inside(folder,asset)
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(inside(self.base,asset).read_bytes())
                    stage='local_replay'
                    result['local']=local_replay(folder,folder/'local',s['expected_checks'],s.get('top','TopModule'),s.get('assets',[]))
                except Exception as exc:
                    result.update(status='EXTRACTION_OR_LOCAL_ERROR',**paths.error_record(exc,stage))
            stage='result_persist'
            save(folder/'result.json',result)
            stage='stop_persist'
            if result['status']!='GENERATED_UNVERIFIED' or result.get('local',{}).get('infrastructure_stop'):
                save(self.state/'STOP.json',{'reason':'LOCAL_INFRASTRUCTURE_FAILURE' if result.get('local',{}).get('infrastructure_stop') else result['status']})
            return result
        except Exception as exc:
            diagnostic=dict(paths.error_record(exc,stage),schema=RESULT_SCHEMA,status='UNKNOWN',send_attempted=sent,slot_id=slot_id,manifest_sha256=self.identity,request_sha256=result.get('request_sha256'),recovery='NO_RESPONSE',storage_errors=[])
            if folder is not None:
                if env is not None:
                    # A separately preflighted short path is a fallback, never a retry.
                    safe=secret not in json.dumps(env,ensure_ascii=False)
                    diagnostic['recovery']='SUPPRESSED_SECRET' if not safe else 'PERSIST_FAILED'
                    if safe:
                        diagnostic['response_sha256']=digest(canonical(env))
                        try:
                            save(self.recovery_path(slot),dict(diagnostic,transport_response=env))
                            diagnostic['recovery']='SAVED';diagnostic['recovery_path']=str(self.recovery_path(slot))
                        except Exception as fallback:
                            diagnostic['storage_errors'].append(paths.error_record(fallback,'recovery_persist'))
                for path,value in [(folder/'result.json',dict(result,**diagnostic)),(self.state/'STOP.json',dict(diagnostic,reason='UNKNOWN_NO_RETRY'))]:
                    try:
                        if not path.exists():save(path,value)
                    except Exception as failure:diagnostic['storage_errors'].append(paths.error_record(failure,'failure_receipt_persist'))
            raise DispatchFailure(diagnostic) from None
        finally:
            lock.unlink()

def extract(text,top):
    # Only frozen extractor definitions; no import side effects or prompt changes.
    path=ROOT/'rtl_lab.py'
    deps=read(ROOT/'console_dependencies.json')
    require(sha(path)==deps['rtl_lab.py'], '提取器源码变化')
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('LabError','extract_rtl')]
    ns={'re':re}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<frozen-extract>','exec'),ns)
    return ns['extract_rtl'](text,top)

def wsl_path(path):
    p=str(Path(path).resolve()).replace('\\','/')
    require(re.match(r'^[A-Za-z]:/',p) is not None,'需要本机盘符路径')
    return '/mnt/'+p[0].lower()+p[2:]

def process(argv,folder,label,timeout):
    """Reuse bounded audited process manager; stdout capped there, no secrets in env."""
    path=ROOT/'rtl_lab.py'
    require(sha(path)==read(ROOT/'console_dependencies.json')['rtl_lab.py'],'本机进程适配器变化')
    import rtl_lab
    env={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP','PATH','USERPROFILE') if k in os.environ}
    result=rtl_lab.run_process(argv,folder,timeout,env=env)
    save(folder/(label+'.json'),result)
    return result

def local_replay(source,output,expected_checks,top='TopModule',assets=()):
    source,output=Path(source),Path(output)
    require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',top),'top 无效')
    hashes={n:sha(source/n) for n in ('dut.sv','testbench.sv','reference.sv')}
    output.mkdir(parents=True,exist_ok=False)
    for n in hashes:(output/n).write_bytes((source/n).read_bytes())
    for name in assets:
        src=inside(source,name);dst=inside(output,name)
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());hashes[name]=sha(src)
    save(output/'input-lock.json',hashes)
    compile_result=process(['D:/iverilog/bin/iverilog.exe','-Wall','-Winfloop','-Wno-timescale','-g2012','-s','tb','-o','sim.vvp','dut.sv','testbench.sv','reference.sv'],output,'compile',15)
    result={'fixed_test':'COMPILE_ERROR','synthesis':'NOT_RUN','source_hashes':hashes,'expected_checks':expected_checks,'model_calls':0,'infrastructure_stop':False}
    if compile_result['timeout'] or compile_result.get('output_limit'):
        result.update(fixed_test='INFRASTRUCTURE_ERROR',infrastructure_stop=True)
        save(output/'result.json',result);return result
    if compile_result['returncode']==0 and not compile_result['timeout']:
        sim=process(['D:/iverilog/bin/vvp.exe','sim.vvp'],output,'simulate',10)
        result.update(simulation_verdict(sim['stdout'],sim['returncode'],expected_checks))
        if sim['timeout'] or sim.get('output_limit') or result['fixed_test']=='TOOL_OR_RECEIPT_ERROR':
            result['infrastructure_stop']=True
    if result['infrastructure_stop']:
        save(output/'result.json',result);return result
    script='read_verilog -sv dut.sv\nhierarchy -check -top '+top+'\nproc\ncheck -assert\nsynth -noabc -top '+top+'\ncheck -assert\nwrite_json netlist.json\nwrite_verilog -noattr netlist.v\n'
    (output/'synthesis.ys').write_text(script,encoding='utf-8',newline='\n')
    try:
        synth=process(['wsl.exe','-d','Ubuntu','--exec','sh','-c','cd "$1" && exec yosys -T -s synthesis.ys','console',wsl_path(output)],output,'synthesis',90)
        result['synthesis']='SYNTH_PASS' if synth['returncode']==0 and not synth['timeout'] and (output/'netlist.json').exists() else 'SYNTH_FAIL'
        if synth['timeout'] or synth.get('output_limit') or synth['returncode'] in (126,127,4294967295):result['infrastructure_stop']=True
    except (OSError,ValueError):result.update(synthesis='ENVIRONMENT_ERROR',infrastructure_stop=True)
    require(all(sha(source/n)==h and sha(output/n)==h for n,h in hashes.items()),'原始输入发生变化')
    save(output/'result.json',result)
    return result

def simulation_verdict(text,code,expected):
    matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$','\n'.join(text.splitlines()),re.M)
    if code!=0 or len(matches)!=1 or 'TIMEOUT' in text.upper():return {'fixed_test':'TOOL_OR_RECEIPT_ERROR'}
    errors,count=map(int,matches[0])
    return {'fixed_test':('FIXED_TEST_PASS' if errors==0 else 'FUNCTION_FAIL') if count==expected else 'CHECK_COUNT_DIFFERENT','mismatches':errors,'samples':count}

def validate_saved_inputs(row):
    """Bind saved RTL to original response and TB/reference to frozen input locks."""
    require(not row.get('assets'),'学校三文件适配暂不支持附加 assets；拒绝静默丢弃')
    source=Path(row['job_dir']);result_path=Path(row['result_path'])
    r=read(result_path);request=source/'request.json';envelope=read(source/'transport-response.json')
    require(sha(request)==r['request_sha256']==envelope['request_sha256'],'原槽请求/执行回执绑定失败')
    require(envelope.get('outcome')=='HTTP_OK','缺完整原始模型响应')
    if envelope.get('raw_body_sha256'):
        require(digest(envelope['body'].encode())==envelope['raw_body_sha256'],'原响应body哈希不符')
    body=json.loads(envelope['body']);obj=read(request)
    if row['dataset'] in HISTORY:expected_provider='OpenAI'
    else:
        imported=Package(row['manifest_path'])
        expected_provider=imported.models[obj['model']]['response_provider']
    require(body.get('model')==obj['model'] and body.get('provider')==expected_provider,'原响应模型身份不符')
    raw=body['choices'][0]['message']['content']
    require((source/'model-output.txt').read_bytes()==raw.encode(),'原模型输出被替换')
    require((source/'dut.sv').read_bytes()==extract(raw,row.get('top','TopModule')).encode(),'保存RTL不再是原模型回复提取结果')
    if row['dataset'] in HISTORY:
        batch_rel,exe_rel=HISTORY[row['dataset']];batch=ROOT/batch_rel
        # Hard historical packet anchors, copied from the frozen executor's binding.
        packet_sha={'new96':'a8f24bd42a5b3d6bf3b4a7f12732dc9aa6f601347862f5538be61243677fecee','old240':'72094112b5c0f6b72e920ad8d362c78ee5e302ee758b1e2de90c7c120b062d39'}[row['dataset']]
        require(sha(batch/'packet-lock.json')==packet_sha,'历史packet锁变化')
        packet=read(batch/'packet-lock.json')
        if row['dataset']=='new96':
            require(sha(batch/'B-lock.json')==packet['B-lock.json'],'原输入锁变化')
            lock=read(batch/'B-lock.json');base=batch/'B'
        else:
            require(sha(batch/'calibration-plan.json')==packet['calibration-plan.json'],'原校准输入锁变化')
            lock=read(batch/'calibration-plan.json')['input_bindings'];base=batch
        for dest,ext in [('testbench.sv','test.sv'),('reference.sv','ref.sv')]:
            name='originals/dataset_spec-to-rtl/'+row['task']+'_'+ext
            require(sha(base/name)==lock[name]==sha(source/dest),'保存测试/参考与原冻结输入不符')
        reservation=ROOT/exe_rel/'runtime/live-run/reservations'/(row['id']+'.json')
        require(read(reservation)['request_sha256']==sha(request),'原预约凭据不符')
    else:
        package=Package(row['manifest_path'])
        require(package.identity==row['manifest_sha256'],'新批清单变化')
        slot=next(s for s in package.slots if s['id']==row['id'])
        require(not slot.get('assets'),'学校三文件适配不支持附加 assets')
        require(sha(inside(package.base,slot['request']))==sha(request),'冻结请求与原执行不符')
        for dest,key in [('testbench.sv','testbench'),('reference.sv','reference')]:
            require(sha(source/dest)==package.data['files'][slot[key]],'保存输入与冻结包不符')
    return {n:sha(source/n) for n in ('dut.sv','testbench.sv','reference.sv','request.json','transport-response.json','model-output.txt')} | {'result.json':sha(result_path)}

def school_history():
    rows=[]
    path=ROOT/'validation/next96-school-single-v1/return-audit.json'
    if path.exists():
        r=read(path);rows.append({'slot':25,'tool':'dc','stage':'synthesis','status':r['status'],'source':str(path)})
    path=ROOT/'validation/next96-dc-gatesim-v1/returned-v1/result.json'
    if path.exists():rows.append(dict(read(path),slot=25,tool='xcelium-dc',stage='fixed_test',expected_samples=213,source=str(path)))
    path=ROOT/'validation/next96-commercial-remaining-v1/return-audit.json'
    if path.exists():
        for r in read(path):rows.append(dict(r['result'],slot=25,tool=r['key'],stage='fixed_test',expected_samples=213,source=str(path)))
    path=ROOT/'validation/console-school-four-slot025-v1/return-audit.json'
    if path.exists():rows.append(dict(source=str(path),stage='four_tool_read_only_audit',audit=read(path),note='VCS212/Xcelium211 vs 213 remains CHECK_COUNT_DIFFERENT; no automatic mapped netlist simulation'))
    return rows
