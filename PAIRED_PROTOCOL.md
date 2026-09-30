# 固定错误状态表的配对反馈实验（2026-10-01）

本协议在真实生成前冻结。本轮研究的是：**同一模型收到同一张错误状态表时，公开可执行反馈能否提高最终 RTL 的修复率？** 这是条件修复实验，不是端到端生成准确率评测，也不是完整 FYP 的最终验收。

## 设计与规模

| 阶段 | 固定错误表 | 模型 | 条件 | 重复 | 新调用上限 |
|---|---:|---:|---:|---:|---:|
| A：配对机制验证 | 4 | 2 | 2 | 2 | 32 |
| B：新题族扩展 | 8 | 2 | 2 | 2 | 64 |

总上限 **96 次新模型调用**，并发 2，仍用 gpt-5.6-sol / gpt-5.6-terra、reasoning=low、每次超时 180 秒。沿用已有 ChatGPT 登录，不购买额度，不使用用量重置。CLI 内部重连不可视为可观测的额外 turn；token、缓存和推理开销原样记录，不声称等费用。

每个配对使用完全相同的规格、接口、公开例子、错误表字节和模型 ID。control 不提供执行结果；feedback 增加由公开例子、复位契约、JSON 结构检查得出的诊断。两组均允许根据原规格修正表，均只生成一次 RTL；不增加第三条件，不事后挑选最佳样本。条件顺序交替，两次调用可并行，CLI 未暴露共享随机种子。

初始错误表复用或人工构造，因此本轮每个分支只消耗一次新调用。保留历史自然表的来源和成本记录，不把历史生成说成免费。本次 96 次不包括此前已完成的 60/48 次研究。

## 错误表与数据划分

- A：保留此前真实的 1001 重叠回退错误，并在同一规格上注入同步复位、错误复位极性、提前输出三种故障。真实错误与注错分开报告，不能将四张表当成四个独立题族。
- B：四个新增开发题族：锁存报警、事件奇偶状态、请求延迟应答及冷却、具有不同升降阈值的去抖。每题预先固定两种故障：初始转移错误、非复位状态输出错误。
- 两个候选保留题族：饱和 credit bucket、四位成帧偶校验。只离线核验规格模型、参考实现和判题，不进行模型实验或据生成结果改题。它们是初步候选集，尚不能宣称经过外部专家审核或穷尽去重。
- 这是独立编写的压力测试库，不冒充 VerilogEval/RTLLM 官方分数。原开发集、原模型输出及锁文件不改动。

新题固定输入包括复位隔离的所有长度 1–8 二进制序列，以及固定种子的长序列/中途复位，共 4,608 个输入周期、9,216 次边沿前后检查。状态图解释器与另一份过程/历史式规格 oracle 全部逐项一致后才允许真实实验。所有错误表须在私有图语义检查和实际 Icarus 故障夹具仿真中被检出。

## 判题、统计与扩容门槛

主要指标为修复后 RTL 的规格仿真通过率，分模型、条件、题族、真实/注入故障报告。另报告成对 both_pass、feedback_only、control_only、both_fail；失败保留在分母。表的已知错误、RTL/表一致性及公共反馈可见性单独记录。通过规格测试称“在固定测试上修复”，不声称完整 RTL 形式等价。

仍使用独立 nonce/检查数量凭据；反馈函数不读取私有向量、参考 RTL 或私有反例。模型生成结束后才做私有诊断。每份保留 RTL 后续用 Yosys 单独综合，绑定原结果和 DUT SHA-256；综合不能取代功能正确性。

只有 A 全部完成 32 次成功调用、没有基础设施失败、没有判题器矛盾才进入 B。**不以 A 是否显示反馈有效作为扩容门槛**。所有任务/故障/划分在 A 前锁定。两次重复、四个新增题族仍不足以做广泛优越性结论；不会将每个测试向量或共享题族的错误变体当作独立研究样本。

已有预留而结果未知的调用终结为 INTERRUPTED，不退额度、不自动重发。模型或环境不可用时保存全部已完成结果并停止追加调用，不购买资源或悄悄换模型。成功完成一次有限实验不要求得到正面研究结果。

## 执行命令

```powershell
python -m unittest -v test_lab test_batch test_dev test_fsm test_paired
python paired_study.py init --run-dir runs/paired-a32 --stage A
python paired_study.py run --run-dir runs/paired-a32 --workers 2
python paired_study.py init --run-dir runs/paired-b64 --stage B --previous runs/paired-a32
python paired_study.py run --run-dir runs/paired-b64 --workers 2
wsl -d Ubuntu -- python3 synthesis.py --run-dir runs/paired-a32
wsl -d Ubuntu -- python3 synthesis.py --run-dir runs/paired-b64
python paired_study.py curate --run-dir runs/paired-a32 --destination evidence/paired-a32
python paired_study.py curate --run-dir runs/paired-b64 --destination evidence/paired-b64
```

本轮验收还包括：报告和文献贡献边界、哈希验证、源码归档、GitHub 同步与 CI。验收完毕后按用户明确要求关机，采用不带 `/f` 的正常关机；如未保存应用阻止关机，不能保证物理断电，也不强制丢弃用户数据。
