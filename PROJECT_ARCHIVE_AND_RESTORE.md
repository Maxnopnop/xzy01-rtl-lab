# 项目同步、历史实验清理与新电脑恢复


> 已完成：同步快照 `2d0daad90a541d83593d84215cd0ca8bac7a0934`；GitHub独立下载后 178,774 文件大小及SHA256全部一致、0差异。
> 已按清单删除本机 13,509 文件（32,813,999字节），GitHub原路径完整保留。
> 最新285批次、人工校准、直接first样本及共享源码未删除。环境迁移尚须自行配置工具和密钥。
> 本机Git对象缓存仍可能保存历史内容；这是工作目录清理，不是安全擦除。

日期：2026-10-30。主仓库：https://github.com/Maxnopnop/xzy01-rtl-lab （public）。

## 本次同步范围

按原路径更新 main，同名文件以本次本机快照为准，不另建一份 rtl-batch 副本。
候选同步 178,774 文件，1,074,811,431 字节。
完整逐文件路径、大小、SHA256及排除项见 PROJECT_SYNC_MANIFEST.json。
本仓库根一直对应本机 outputs/rtl-batch；项目外层 work 映射仓库 work；
外层 outputs 的兄弟文件映射仓库 outputs（不包含重复的 outputs/rtl-batch）。
旧版本仍可通过 Git 历史检索；不同实验的原始证据即使内容相同也保留其原路径和出处。

## 保护与例外

用户明确保留最新285份批次：本机仿真/综合已完成，但学校商业工具验证尚未完成。
本次排除整个 exploration/20261030、runtime，以及20261029/rag20、rag300系列和关联publication审查；
精确前缀/文件以清单为准。本次不能用于单独恢复该未完成批次。
密钥、本机config.local配置、账户配额原始快照、Python缓存和学校库不作为可公开同步内容。
包含本机配置的旧ZIP亦排除，不倒改ZIP内容。它们不在删除清单。
Git内部目录不上传；第三方源文件保留许可证和原目录，不复制其.git元数据。
恢复验证只证明纳入清单文件的字节完整，不证明新电脑能免安装运行所有工具。

## 后续引用的实验规则

1. 主线由未修改原规格单次直接生成RTL；不先生成IR/计划，不提供候选IR、答案或私有测试。
2. 同题同条件各模型完整实际提示词及参考内容逐字相同；有/无RAG的预声明差异单列。
3. 原题、输入、测试、评分与模型原始RTL不改；模型失败/未知/未执行保留，不能挑结果。
4. RAG先独立冻结来源、片段、检索与包装，再接触评测题；未经许可不得依考题或历史成绩调优。
5. 有限清单、无自动重试、换模型、补样、扩批；记录真实token/费用和基础设施失败。

## 哪些本机旧文件可以清理

删除清单为 HISTORICAL_LOCAL_CLEANUP_MANIFEST.json，共 13,509 文件。
这些文件仍完整留在GitHub原路径，本机清理不是从GitHub删掉历史证据。

|范围|明确不符合的原因|
|---|---|
|FSM48运行及结果副本|计划/IR在前，RTL在后；部分第二阶段提示随模型输出变化|
|paired A32/B64运行及结果副本|给生成器候选IR进行条件修复，非纯规格直接RTL|
|R2 factorial20运行|候选IR＋反馈/重新生成协议|
|R4 prepared-v2|意图、首次RTL、反馈/再生成的多阶段流程|
|R5/R6 prepared任务中的structured分支|先意图/IR再RTL|
|R5/R6 direct非first分支|包含前次候选或反馈再生成，非单次直接基线|

保留：R5/R6 direct first、R3、pilot60（证据不足不能判违规）；163/3119人工故障、
延迟触发、握手、事务域对齐、R1b/R1c和学校工具验证（工程证据不等于违规）；
共享源码、协议、审计报告、校准和离线mock。失败本身绝不是删除理由。
统计时不得把旧多阶段/人工校准冒充当前主线模型收益。

## 新电脑恢复

安装 Git 和 Python 3.10+。在希望保存项目的位置执行（这里只下载和校验，不调用模型）：

```powershell
git -c core.longpaths=true -c core.autocrlf=false clone https://github.com/Maxnopnop/xzy01-rtl-lab.git rtl-batch
Set-Location rtl-batch
python -B verify_project_restore.py --root . --output ../restore-verification.json
```

输出 passed=true 才表示本次清单全部匹配。精确恢复本轮应先 checkout 同步提交，
提交号和远端核验记录见 PROJECT_SYNC_RECEIPT.json（完成后写入）。
仓库必须位于短路径，Windows启用长路径；不要依赖ZIP下载的行尾转换或手动复制。

本机结构如需一致：把本仓库放入 项目目录/outputs/rtl-batch，
仓库 work 复制回 项目目录/work；仓库 outputs 内的兄弟文件复制到 项目目录/outputs。
不必保留原电脑E盘绝对路径，但旧配置中的绝对路径需要重新配置，不能宣称全部脚本零改动即用。

运行环境另行准备：requirements.txt 指定Python标准库；本机仿真需Icarus/iverilog/vvp，
综合需Yosys（原流程部分使用WSL）。控制台入口Open-Lab-v3.cmd，参考CONSOLE_MULTIMODEL_V3.md。
OpenRouter密钥在新电脑由用户重新输入，不能从Git恢复。学校VCS/Xcelium/DC/Genus、许可证及
工艺库仍使用学校平台，参考ECE_WORKFLOW.md及ECE_SYNTHESIS_GUIDE.md。旧release不等于新运行授权。
最新285批次不在本次快照，待完成后应单独补同步。

## 核验与删除门槛

采用从GitHub独立clone（非本地复制、无本地对象共享），按SHA256与大小核对全部纳入文件。
删除前再次检查当前本机文件与远端恢复件一致；若有变更、缺失或不能恢复则不删除。
确切上传提交、核验和已删除数量以 PROJECT_SYNC_RECEIPT.json 为准；本说明本身不是成功回执。
本地Git对远端保留但本机清理的文件使用skip-worktree，避免普通git add -u把归档从远端删除。
需要恢复这些文件时：取消对应skip-worktree后 git restore --source=同步提交 -- 对应路径。

## 临时核验副本保留说明

原工作目录清单中的13509文件已删除，GitHub归档保留。但自动执行策略拒绝对本次两个临时clone目录递归删除，仅返回`blocked by policy`，未说明更具体原因；未绕过限制。因此项目外层`.planning/historical-github-archive-20261030/stage`与`restore`仍有本次核验副本。它们是临时副本，不是新的实验或主仓库中的重复目录。本机Git对象缓存也可能保有历史，不能宣称本机所有副本已擦除。
