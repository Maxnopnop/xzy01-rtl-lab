# Working on XZY01 RTL Lab

- Latest user experiment constraint (2026-10-16): follow `FYP_FIXED_INPUT_RTL_RULES.md`. Preserve original task inputs and tests byte-for-byte; identical actual prompt content across models for each task; this new mainline uses one model call directly producing RTL, without candidate IR or feedback. Freeze and coordinator-review the finite new design before execution; preserve all historical evidence.

- Read README.md and ARCHITECTURE.md before editing the runner.
- Keep model generation, task/testbench definitions, scheduling and simulation adapters separable.
- Use Python 3.10+ standard library unless a dependency materially improves the experiment.
- Never expose credentials. Exclude machine-local configs, raw account logs, runs and generated binaries from Git.
- Treat generated RTL as untrusted input. Keep the fixed testbench and vector hashes independent of the generator.
- Never count offline fixtures or synthetic HTTP/commercial-tool tests as real model/EDA evidence.
- Existing ECE shared VDI: no SSH, no supported batch EDA service, no EDA scheduler. Export one-case manual scripts until new explicit school permission exists.
- Do not change an active experiment's source. Create a new run after code/task/tool changes.
- Run `python -m unittest -v test_lab test_batch test_dev` for meaningful runner changes. Synthesis tests require native Yosys in WSL/Linux or a native Windows installation.
- FSM study changes also require `test_fsm`; preserve its two-call cap, public/private checker separation, and no automatic retries after unknown outcomes.
- Keep dev10 source/split locks and adapted-benchmark labels. Never mix development tasks or near duplicates into the final set.
- Synthesis review must bind the original result and RTL hashes; never overwrite model output or silently repair baseline failures.
- Real Codex/API experiments consume account usage; keep concurrency/call caps explicit and preserve requested model IDs.
- Keep Chinese user documentation and evidence summaries accurate about what was actually executed.


## 2026-10-24 用户新增约束：禁止未经许可利用历史实验经验调优
- 新实验未经用户明确允许，不得利用此前实验结果、错误分析或经验总结修改 RAG 资料库、片段、检索规则/参数/排序/拼接方式、提示词或题目（含输入与测试数据）。
- 可以只读分析并提出修改建议；建议不构成修改或执行授权。需要改变时先列明具体变更与依据，取得用户明确允许，再另版本冻结审核；保留原证据。
- 此约束适用于所有后续新实验；不得将本轮 RAG 帮助/变差案例暗中用于下一轮调优。本轮冻结内容不变。

## 2026-10-24 最新规则：本轮RAG设计不得以考题为依据
- 用户要求独立设计RAG：禁止根据历史或新评测题、参考答案、测试台、模型失败、成绩、检索结果补写/删选知识、调检索、改提示词；本轮不以“转为开发集”作为考题驱动调优的例外。
- 方法依据限于公开通用语言/硬件文档和一般检索算法。先冻结来源版本/许可、片段规则/内容、算法参数/排序/预算、提示包装及选题规则，再接触新候选题；冻结后只按规则自动检索，不人工换段、不回调方法。
- 新题按来源/契约/参考有效性与历史及语义近重复排除筛选，不能按RAG命中好坏或预期成绩挑题。全部排除理由保留；不宣称公开题为模型训练未见。
- 新设计另存版本，历史证据不变。同题同条件三个指定模型完整提示/参考逐字相同，单次直接生成RTL。当前授权设计、筛题及控制台集成离线验证，新模型批次仍待冻结审核；不自动调用、重试、替换、扩批或学校批处理。
