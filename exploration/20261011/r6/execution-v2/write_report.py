"""Render report from original sealed results and read-only audit; no model calls."""
import json
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parent;BASE=OUT.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def fmt(v):return 'UNKNOWN' if v is None else str(v)
def report():
    a=read(OUT/'actual-analysis.json');summary=a['summary'];rows=read(BASE/'runs/prepared-v2/results.json')
    out=OUT/'RESULTS.md';assert not out.exists(),'Never overwrite report'
    unknown=len(a['unknown_reservations']);pending=len(a['pending']);limit=len(a['input_limit_no_dispatch'])
    lines=['# R6 单次有限批结果（完成后停止）','',
      f"本批状态 **{a['batch_state']}**：48固定槽中 **{a['clean_completed_calls']} 次clean完整返回、{unknown} 个异常/未知预约、{pending} 个未启动、{limit} 个输入限制未调用**。原driver dispatch为 `{a['dispatch']['status']}`。仅运行总控放行的engineering-v2/runner.py → runs/prepared-v2，精确SHA `{a['plan_sha256']}`；未运行v1/R5、不重发/补样/改题/切模型/扩批。",'',
      '## 服务与保全','',
      f"首4production服务gate：{a['service_gate']}。各clean返回均单CLI thread/单clean completed，原chunk/nonce/exit/final/prompt/父样本/模板/model核对通过；不是功能择样。实际CLI版本：{json.dumps(a['versions'],ensure_ascii=False)}；exe SHA：{json.dumps(a['exe_hashes'])}。requested model=gpt-5.6-sol/low，后端snapshot未暴露。",'',
      f"只读审计PASS：{a['source_bindings']}冻结源、{a['preparation_bindings_preserved']}准备绑定、{a['prior_bindings_preserved']}历史绑定未变，当前运行{a['run_seal_files']}文件精确集合封存。实际本批compile {a['compile_calls']} / simulate {a['simulate_calls']}，{a['simulated_event_checks']}原事件检查；nonce/退出/DUT/TB/vector和固定公开/隐藏期望、真实IR期望绑定。审计0模型/0模拟/0judge重跑。",'',
      '## 四臂与各阶段','',
      '| 策略 | PASS / 主分母 | 全状态 | 计划机会 | 实际预约半共享 | 已知完成半共享 |',
      '|---|---:|---|---:|---:|---:|']
    names={'structured_regeneration':'S-R','structured_feedback':'S-F','direct_regeneration':'D-R','direct_feedback':'D-F'}
    for k,name in names.items():
        l=a['ledger'][k];st=l['strategy'];lines.append(f"| {name} | {st['passes']} / 6 | {json.dumps(st['statuses'],ensure_ascii=False)} | 18 | {fmt(l['reserved_half'])} | {fmt(l['known_completed_half'])} |")
    lines+=['','S=真实模型IR→首次RTL→最终；D=D1→无条件D2→最终。D2固定父，不select-best；F两表示仅同公开RTL_spec信息，R无执行结果，IR专属私有诊断仅后评分。每策略18机会/半共享计划12，不是严格token公平或纯格式单因素。','',
      '| 阶段 | 原状态计数 |','|---|---|']
    for role,statuses in a['role_statuses'].items():lines.append(f'| {role} | {json.dumps(statuses,ensure_ascii=False)} |')
    lines+=['','| 任务族 | 全流水线槽状态（不是最终策略通过率） |','|---|---|']
    for family,statuses in a['by_family'].items():lines.append(f'| {family} | {json.dumps(statuses,ensure_ascii=False)} |')
    effects=summary['effects'];lines+=['',f"F/R配对：help **{effects.get('help',0)}**、harm **{effects.get('harm',0)}**、no_change **{effects.get('no_change',0)}**、inconclusive **{effects.get('inconclusive',0)}**。no_change仅表示两者功能PASS/非PASS分类无改善，不等于RTL相同或所有行为等价。",'']
    functional={'PASS','FUNCTION_FAIL','COMPILE_FAIL','RTL_REJECTED','EXTRACTION_ERROR','IR_INVALID','UNSUPPORTED','INPUT_LIMIT'}
    comparison=Counter()
    for pair in summary['representation_pairs']:
        s,d=pair['structured'],pair['direct']
        category='inconclusive' if s not in functional or d not in functional else 'S_pass_D_nonpass' if s=='PASS' and d!='PASS' else 'D_pass_S_nonpass' if d=='PASS' and s!='PASS' else 'same_pass_class'
        comparison[category]+=1
    lines+=[f"同case/同最终arm的S/D配对：{json.dumps(dict(comparison),ensure_ascii=False)}。这是工作流程对照；无显式IR不表示无内部思考，D不可归因理解阶段。",'',
      '## 自然三路偏差与研究结论','']
    obs=Counter(x['category'] for x in a['observations'])
    lines+=[f"S原三路观察{len(a['observations'])}项（复用6份真实IR，并非18个独立意图样本）：{json.dumps(dict(obs),ensure_ascii=False)}。IR_spec/RTL_spec/RTL_intent都是原固定判据；分类仅可观察阶段关联，不能唯一证明内部理解错误因果。IR format/unsupported/INPUT_LIMIT均在主分母，不因不可定位删除。",'']
    if effects.get('help',0)==0:
        lines+=['本批没有观察到公开执行反馈的准确率改善；保留harm及无变化/不可判定配对，不能推断反馈普遍无用。','']
    else:lines+=['本批存在固定开发判据上的自然help配对；必须连同harm、完整分母、任务簇和受限判据解释，不能外推普遍改善。','']
    if not comparison.get('S_pass_D_nonpass',0):lines+=['最终配对没有观察到显式IR流程优于两次直接RTL流程的功能通过分类；同PASS/非PASS分类不证明一般等效。','']
    diverged=[o for o in a['observations'] if o['category'] not in ['ALL_MATCH','NOT_ASSESSABLE']]
    if diverged:
        lines+=['自然偏差索引：','', '| 样本 | IR_spec | RTL_spec | RTL_intent | 类别 |','|---|---|---|---|---|']
        for o in diverged:lines.append(f"| {o['id']} | {o['intent_spec']} | {o['rtl_spec']} | {o['rtl_intent']} | {o['category']} |")
        lines+=['']
    else:lines+=['没有自然可评分三路偏差样本；人工负例校准不能替代自然阶段定位收益。','']
    failures=[]
    for row in rows:
        for kind,check in (row.get('judge') or {}).items():
            if check.get('status') not in ['PASS','NOT_ASSESSABLE']:failures.append(dict(id=row['id'],kind=kind,status=check['status'],message=check.get('message'),mismatches=check.get('mismatches',[])[:3]))
    if failures:
        lines+=['原失败/不可支持证据（最多列前8项，完整保留在results/hidden-judge中）：','', '```json',json.dumps(failures[:8],ensure_ascii=False,indent=2),'```','']
    lines+=['## 已知/未知费用账','',
      f"已知clean返回usage：{json.dumps(a['known_completed_usage'])}；clean返回缺失字段计数：{json.dumps(a['missing_known_provider_fields'])}。整批已预约provider usage：{json.dumps(a['total_provider_usage']) if a['total_provider_usage'] is not None else 'UNKNOWN'}；金额 **UNKNOWN**。未知预约usage保持null，不填0、不由标价/订阅/信用余额估算费用。cached input在input内，reasoning在output内，不重加。",'',
      '| 策略 | 已知半共享 input | output | cached input | reasoning output（output内） |',
      '|---|---:|---:|---:|---:|']
    for k,name in names.items():
        u=a['ledger'][k]['known_half_usage'];m=a['ledger'][k]['missing_provider_fields'];lines.append(f"| {name} | {fmt(u['input_tokens'])} | {fmt(u['output_tokens'])} | {fmt(u['cached_input_tokens'])} | {fmt(u['reasoning_output_tokens'])} |")
        if any(m.values()):lines.append(f"\n{name}上表仅已知字段子账，缺字段{json.dumps(m)}不计作0或完整账。\n")
    lines+=['',f"上述子账按shared/2+branch分摊并与实际唯一clean usage守恒；计划机会不冒充已预约数。已知CLI进程时间合计{a['cli_seconds']:.3f}s、adapter合计{a['adapter_seconds']:.3f}s；不是服务端账单耗时。实际prompt字节范围{a['prompt_byte_range']}，不证明256KiB服务上下文边界。",'',
      '## 限制与停止','',
      '全部是参与本轮设计/校准的原创development，候选保留集为空；同作者三路径参考存在共误读，非外部独立作者/独立最终集。binary/#2/固定参数/有界短轨迹，除法正常16×16有限域不覆盖全部暂停/复位交错；覆盖矩阵已记不可观察规则和缺口，无无界证明/PPA。工程人工验收不是自然模型收益或生产恢复/后代树清理/桌面停止根因修复。默认回归34测试3failure/1error/2skip仍保留；此次未隔离重试或重复回归。','',
      '本批执行及报告完成即停，交总控独立核验原stream/CLI/评分/预算/研究价值；不追加新轮、扩批、补样或重判旧模型RTL。原始结果在 `../runs/prepared-v2/results.json`、`summary.json`、`evidence-lock.json`；本报告只在execution-v2新目录写入。', '',
      '只读审计首版audit-invocation-v1因job根目录exact-prompt路径假设失败；原脚本/完整stdout/stderr/receipt封存，新analyze_v2只修正审计路径，不改原批结果或重跑判题。审计入口：[actual-analysis.json](actual-analysis.json)、[service-gate-audit.json](service-gate-audit.json)、[release.json](release.json)、[analyze_v2.py](analyze_v2.py)。用analyze_v2.py --verify复算只读核验，不覆盖既有审计。']
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('RESULTS written from original sealed evidence; no model/simulator calls')
if __name__=='__main__':report()
