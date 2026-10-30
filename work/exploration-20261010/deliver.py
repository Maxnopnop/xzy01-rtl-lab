"""Create a data-bound Chinese report and verified local archive."""
import json
from pathlib import Path
import zipfile
import compound_probe as probe

root = probe.HERE
read = lambda p: json.loads((root/p).read_text(encoding='utf-8-sig'))
double = read('evidence-v1/summary.json')
triple = read('evidence-triple-v1/summary.json')
extension = read('evidence-extension-v1/summary.json')
verification = read('verification.json')
assert verification['status']=='PASS'
lines = ['XZY01：公开反馈语义覆盖探索', '日期：2026-10-10（Asia/Shanghai）', '',
         '本轮结论',
         '公开契约v2对本轮固定状态空间的双处和三处故障均有效；增加实现状态后，仍可构造通过公开例子的错误实现。',
         '建议研究重点转向：在明确实现状态上限、信息预算和调用预算下，比较例子选择与反馈形式如何影响错误检出和真实模型修复。', '',
         '实际执行与分母',
         f"双字段修改：{double['total_pairs']}个变体，{double['faults']}个非等价故障，{double['equivalent']}个等价。",
         f"三字段修改：{triple['total_pairs']}个变体，{triple['faults']}个非等价故障，{triple['equivalent']}个等价。",
         f"合计：{double['total_pairs']+triple['total_pairs']}个变体，{double['faults']+triple['faults']}个非等价故障。",
         '五个开发题族；完全穷举声明的修改集合，同字段互斥修改排除，未采样、未挑选正结果。',
         '公开v2保持原文件和哈希；没有针对这轮结果补例子。候选未见题没有参与实验。', '',
         '开发题族                 双故障数/原漏检/v2漏检    三故障数/原漏检/v2漏检']
for a,b in zip(double['coverage'],triple['coverage']):
    assert a['task']==b['task']
    lines.append(f"{a['task']:24} {a['faults']:5}/{a['v1_missed']:4}/{a['v2_missed']:2}                 {b['faults']:5}/{b['v1_missed']:4}/{b['v2_missed']:2}")
lines += ['', f"原公开契约共漏检{sum(c['v1_missed'] for c in double['coverage']+triple['coverage'])}个非等价故障；新版漏检0。",
          '两处/三处高阶故障仍与拟合单处故障时使用的开发题族相同，不能称为未见题泛化。', '',
          '扩展状态的可执行反例（明确标记为人为对抗夹具）',
          '每题寻找最短、字典序最小的未公开输入前缀，复制其路径状态，并在终点翻转一个输出；分支离开路径后恢复原图行为。',
          '该构造只用于展示有限公开检查的边界，不代表LLM自然生成时会采用这种策略。']
for case in extension['cases']:
    lines.append(f"{case['task']}：状态{case['reference_states']}→{case['candidate_states']}，输入{case['bits']}；正确{''.join(map(str,case['expected']))}，错误{''.join(map(str,case['observed']))}；PUBLIC_CHECK_PASS；精确图不等价；Icarus固定测试{case['fixed_test']['status']}，反例测试{case['witness_test']['status']}。")
lines += ['', '实际RTL执行：30次Icarus评估，包括两轮各五个正确参考×规格/一致性检查（20次），五个扩展状态故障×固定规格/最短反例检查（10次）。',
          '44,048个高阶变体执行的是精确抽象图检查和公开轨迹解释；没有将它们全部编译成RTL或运行44,048次仿真。',
          '新增LLM/API调用0；商业EDA调用0；费用支出0（未启动付费服务调用）。', '',
          '独立复验',
          'verify_evidence.py用独立颜色划分细化算法重新判断全部变体的等价性和最短反例长度；公开轨迹用独立解释器复验。',
          '变体数用各字段修改数的生成多项式系数独立计算，检查无缺失、无重复、确实修改2或3处。',
          '三套证据文件清单/哈希、源码、公开契约和bank-lock全部通过审计。扩展状态DUT与实际仿真记录哈希一致。',
          'verification.json记录PASS。脚本没有改动既有运行器；原Git工作区的未提交改动保持原样。', '',
          '轨迹预算探索',
          'summary.json中的1至10深度扫描由精确最短反例推导，包含复位元数据/初始输出检查；不是独立执行全部轨迹。',
          '例如序列题双处故障：v2用11条例子、56输入周期检出全部1209个故障；穷举深度7需128条、896输入周期（不含复位）才检出同一故障集。',
          '这只表明此声明故障集的测试效率差异；并非v2具有完整性保证，也不是等token/等费用模型实验。', '',
          '与已有工作的关系（2026-10-10核查原论文摘要/项目说明）',
          'AutoFSM已研究IR、自动翻译和SystemC测试反馈。仅使用IR与反馈不能直接主张创新。',
          'https://arxiv.org/abs/2512.11398',
          'VeriRefine已研究规格细化、结构审计及按理解/编码阶段分流修复。阶段定位机制需要相对其形成具体差异。',
          'https://arxiv.org/abs/2607.18519',
          'LLM-FSM提供可变状态复杂度的FSM评估方向，可进一步核查公开源码、许可、数据划分和与当前题库的重叠。此次未下载或采用其数据。',
          'https://arxiv.org/abs/2602.07032',
          '完整FSM测试策略的形式化资料涵盖W/Wp等方法。下一步应核对方法前提并实现对照；本轮没有实现或证明W/Wp方法。',
          'https://isa-afp.org/entries/FSM_Tests.html', '',
          '后续实验优先级',
          '1. 开发集工具探索：从同一规格产生固定例子、随机例子、状态区分例子，比较相同轨迹/周期预算下的覆盖；采用状态增加、重命名、不可达状态等故障集合。',
          '2. 开发集模型实验：预先冻结原/新例子×无/有执行反馈的2×2消融，明确模型ID、总调用上限、并发、token上限、未知结果停止规则；保留自然错误来源。',
          '3. 建立独立新题族与最终划分；将已用于观察和方法调整的题族继续留在开发集。',
          '4. 正式端到端比较，应把首次生成、修复、基础设施缺失、功能正确与综合正确分开统计，并按独立题族分析。',
          '5. 学校商业综合证据按现有单案例协议回收。当前授权可支持扩展探索，但本轮未启动学校共享VDI批作业或更改学校运行方式。', '',
          '本机资源',
          '资源清单见resources.json：24逻辑处理器，约31.43GiB内存，RTX 5060 Laptop GPU；本轮CPU任务无需GPU。',
          '已使用本机Icarus与Codex捆绑Python。WSL Ubuntu存在，工具可用性查询另存tool-resources.txt。', '',
          '复现（PowerShell，工作目录为此报告所在目录）',
          "$p = 'C:\\Users\\A\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'",
          '& $p verify_evidence.py',
          '& $p compound_probe.py --out evidence-double-replay --simulate',
          '& $p triple_probe.py --out evidence-triple-replay --simulate',
          'extension_probe.py使用固定的新目录，已有证据时拒绝覆盖；如需重跑，应复制到独立实验目录并预先记录新来源/哈希。', '',
          '整个FYP的最终未见题、多模型端到端正式评估、相对近邻的创新贡献和商业PPA验证仍需继续。本轮完成的是一项覆盖边界探索。']
(root/'REPORT.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
planroot = root/'.planning/2026-10-10-rtl-compound-fault-exploration'
(planroot/'task_plan.md').write_text('''# RTL 探索计划 — 2026-10-10

用户授权本机和外部资源探索及大规模实验。本轮有限探索完成。

## 阶段
1. 阅读提案、原规则、历史证据：complete。
2. 双字段3119与三字段40929变体的完整枚举及公开契约比较：complete。
3. 参考及扩展状态故障实际Icarus验证30次：complete。
4. 独立颜色细化/组合计数/公开解释/哈希复验，中文报告和本机证据归档：complete。

## 结果
44048个高阶变体，44046个非等价故障，新版全部检出。5个扩展状态对抗夹具通过公开检查却精确不等价，均由实际Icarus检出。
不更改历史分数、运行器、他人未提交工作；不使用未见题；0新增模型调用。后续研究建议记录于REPORT.txt，未作为已完成模型实验。

## 错误与修正
- 首次命令使用未建立的cwd，先在已有根目录建立后解决。
- python为Windows占位符，改用捆绑Python绝对路径。
''',encoding='utf-8')
with (planroot/'findings.md').open('a',encoding='utf-8') as f:
    f.write('\n高阶总44048，非等价44046，等价2；新版0漏检，原漏982。扩展状态5/5可通过公开例子但实际RTL失败。研究边界是实现状态空间而不仅是修改处数。独立审计全部PASS，详情REPORT.txt。\n')
with (planroot/'progress.md').open('a',encoding='utf-8') as f:
    f.write('\n2026-10-10：三字段、扩展状态实验完成；30次实际Icarus评估；独立复验PASS；报告及本机ZIP归档完成。没有新模型调用、学校EDA、Git同步或关机。\n')
files = [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
         and p.suffix != '.zip' and p.name != 'delivery.json']
archive = root/'exploration-20261010.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for path in files:
        z.write(path, path.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == {p.relative_to(root).as_posix() for p in files}
    for path in files:
        assert z.read(path.relative_to(root).as_posix()) == path.read_bytes()
probe.write(root/'delivery.json',dict(status='PASS', archive_sha256=probe.sha(archive),
             files=len(files), archive_bytes=archive.stat().st_size, graph_variants=44048,
             non_equivalent_graph_faults=44046, adversarial_extension_cases=5,
             real_icarus_evaluations=30, new_model_calls=0))
print((root/'delivery.json').read_text(encoding='utf-8'))
