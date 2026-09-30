# 离线故障覆盖验证协议

2026-10-01。本轮不新增模型调用，检查开发用例和诊断工具是否真的能发现其声称覆盖的错误。冻结旧 paired-v1 数据与所有模型输出，不修改既有分数；候选保留题不参与此次枚举、用例选择或诊断校准。

## 两个可证伪问题

1. 合法 JSON 状态表只错一处时，原公开契约是否都会报错？对五个开发题族，穷举每条转移的其他目标、每个状态的输出翻转、复位类型/极性翻转、复位状态的其他目标，共 163 个单处变体。精确有限图比较用于区分等价与实际故障，再实际编译确定性夹具，检查固定 Icarus 判题和 IR/RTL 一致性。
2. 已知故障发生阶段时，诊断是否返回正确类别？每题运行正确表/正确 RTL、错误表/忠实 RTL、正确表/错误 RTL、错误表/正确 RTL、错误表/不同错误 RTL 五格，共 25 格。均为人工可控夹具，不能充当真实模型样本或自然错误发生率。

## 改进方式与信息隔离

原公开例子有盲点时，从开发图最短反例得到候选输入，再用独立过程 oracle 计算期望输出，按确定性贪心覆盖补充公开例子。不声称用例数全局最少。新增 contracts-v2.json 是显式的开发集拟合产物，不替换旧 contracts，不把拟合后覆盖率当作未见题能力。

公共执行入口 check 只读取给定 profile 的 contract 与候选 JSON，不运行参考图、过程 oracle 或私有判题。生成 profile 的开发程序与使用 profile 的检查步骤必须分开。下一轮真实比较需要两组都收到新版公开例子，并重新冻结运行计划；旧实验不补跑。

每个变体经原固定 Icarus 测试以及其自身 IR 派生的一致性测试。若原测试漏检实际故障，独立保存最短反例诊断；不得悄悄替换过去的判题。全部输入、源码、结果和夹具哈希归档，完整日志留本机。限定单比特、上升沿、Moore FSM；不是任意 RTL 形式证明。

## 命令

```powershell
python mutation_study.py analyze
python -m unittest -v test_mutation
python mutation_study.py run --run-dir runs/mutation-v1
python mutation_study.py curate --run-dir runs/mutation-v1 --destination evidence/mutation-v1
python mutation_study.py verify --evidence evidence/mutation-v1
python mutation_study.py check --contracts evidence/mutation-v1/contracts-v2.json --task sticky_alarm --ir benchmarks/paired-v1/sticky_alarm/reference.json
```

本轮验收：真实仿真完成、诊断格全部一致、旧证据审计仍通过、回归与 CI 通过、报告和备份可复查。不要求获得正面的模型效果结论，不额外消耗 LLM 调用。
