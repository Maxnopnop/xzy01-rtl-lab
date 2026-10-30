# 新96份RTL：综合及综合后仿真验收

2026-10-24完成，范围8题×3模型×2条件×2样本。保留全部96份原始RTL，包括两个功能失败样本；无模型调用、修复、重试、补样或扩批。

| 检查 | 结果 |
|---|---|
| WSL下原RTL复验 | 94通过，2失败；96份均与原Windows实验的错误数和检查分母一致 |
| Yosys通用综合及结构检查 | 96/96通过 |
| 综合后的网表运行原题测试 | 94通过，2失败 |
| RTL与网表的原题测试结果 | 96/96一致（错误数、检查数与通过状态） |
| 综合锁存器单元 | 0份检出 |
| 原题/参考/测试/RTL及冻结方法 | 哈希未变 |

| 模型 | 无RAG：综合通过／网表仿真通过 | 有RAG：综合通过／网表仿真通过 |
|---|---|---|
| Luna | 16/16；16/16 | 16/16；16/16 |
| Terra | 16/16；15/16 | 16/16；15/16 |
| Sol | 16/16；16/16 | 16/16；16/16 |

两个失败均为Prob094 Terra。第27槽无RAG样本1仍160/213次不匹配，第34槽有RAG样本2仍186/213次不匹配；二者综合通过但功能仍错误。综合没有修复模型错误，也未在原测试中引入新增失败。

## 工具和流程

Ubuntu WSL：Yosys 0.52（fee39a3284c90249e1d9684cf6944ffbbcbb8f90），Icarus/vvp 12.0。工具哈希及版本日志见environment.json。复用原rtl_lab.run_process，净化子进程环境、限制日志、超时终止整个POSIX进程组。

每份原始RTL先用WSL Icarus运行原testbench/reference，再执行以下冻结综合流程，最后用相同Icarus和原testbench/reference运行输出netlist.v：

```text
read_verilog -sv dut.sv
hierarchy -check -top TopModule
proc
check -assert
synth -noabc -top TopModule
check -assert
tee -o stat.json stat -json
write_json netlist.json
write_verilog -noattr netlist.v
```

共96次综合、192次编译、192次仿真，480次工具进程成功退出，另3次版本查询。串行执行；每次综合60秒、编译15秒、仿真10秒上限，未发生工具超时或输出超限。每样本原始文件副本、命令、退出码、stdout/stderr、统计及网表均保留在jobs/001至jobs/096。

## 通用单元数

各题12样本的最小–最大值：

| 题目 | 通用单元数 |
|---|---:|
| Prob001_zero | 0（常零连接） |
| Prob019_m2014_q4f | 2 |
| Prob094_gatesv | 10 |
| Prob143_fsm_onehot | 22–23 |
| Prob114_bugs_case | 67–71 |
| Prob087_gates | 8 |
| Prob050_kmap1 | 2 |
| Prob106_always_nolatches | 45 |

这些是Yosys通用单元数量，没有使用标准单元工艺库、ABC映射或面积/时序/功耗模型。不能换算为硅面积或据此认定RAG改善PPA。功能失败样本也在完整分母中，不能用其门数宣传质量优势。

## 验收与边界

独立核验程序verify.py重读96份结果、480条执行记录、原始仿真Mismatches及综合网表统计，验证2512份输出证据哈希和652份本机输入/源码哈希；WSL执行器另核工具哈希，所有源文件执行后未变。见verification.json、summary.json、input-lock.json及evidence-lock.json。准备阶段曾遇Windows反斜杠路径转换错误，在任何EDA执行前修正；prepare-path-error.json保留，此后只执行一轮96样本。

本结果只是固定测试下综合前后一致性，非形式等价证明、非门延时仿真、非独立oracle。Prob143多hot覆盖缺口仍在，不添加测试或更改原分数；其他先前公开题相关性限制仍适用。

下一阶段若要学校DC/Genus工艺映射，需要用户在ECE平台操作并绑定本轮原RTL、真实库角和适用于组合电路的约束。已有历史时钟约束不能直接套用这8题；本轮没有启动学校工具，也未改变学校单例任务。商业仿真VCS/Xcelium同样应作为另存的原题复验结果。
