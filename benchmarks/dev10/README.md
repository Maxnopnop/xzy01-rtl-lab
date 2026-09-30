# 正式开发集 dev10-v1

这是为 XZY01 pilot 冻结的 **VerilogEval 5 题 + RTLLM 5 题**。使用上游规格和参考 RTL，另编写固定向量及独立 Python oracle。它是经过适配的开发子集，不能将成绩称为两个 benchmark 的官方成绩。

原始规格、参考 RTL 和 testbench 的 Windows checkout 副本保存在 `upstream/`，两个项目的 MIT 许可证一并保留。Git checkout 将 LF 转换成了 CRLF；已逐一核对这 30 个文件与固定 commit 的 Git blob，除换行外内容相同，双方哈希见 `upstream-blob-audit.json`。存档字节由 `.gitattributes` 固定，不随以后克隆的平台改写。原始 testbench 用于审计参考，没有作为本次运行的判题器。运行用的适配记录和逐文件 SHA-256 在 `tasks/manifest.json`，全部上游存档文件哈希在 `source-lock.json`。

| 来源 | 固定 commit |
|---|---|
| [NVlabs/verilog-eval](https://github.com/NVlabs/verilog-eval/tree/c498220d0a52248f8e3fdffe279075215bde2da6) | c498220d0a52248f8e3fdffe279075215bde2da6 |
| [hkust-zhiyao/RTLLM](https://github.com/hkust-zhiyao/RTLLM/tree/51ed553d0ffd32797a1a0a13e051656bf302c81f) | 51ed553d0ffd32797a1a0a13e051656bf302c81f |

| ID | 来源任务 | 测试范围 |
|---|---|---|
| ve_addsub | Prob123_bugs_addsubz | 8 位两操作数及加/减操作穷举，零标志 |
| ve_popcount | Prob030_popcount255 | 零/全一、255 个单一位/单零位及固定随机向量 |
| ve_count10 | Prob040_count10 | 模 10 回绕、同步复位及边沿间保持 |
| ve_rotate | Prob105_rotate100 | 100 位左右旋转、装载优先、两种保持使能 |
| ve_fsm | Prob119_fsm3 | 四状态 Moore 转移、异步复位、固定随机序列 |
| rt_comparator | comparator_3bit | 3 位无符号两操作数穷举 |
| rt_counter12 | counter_12 | 模 12 回绕、使能保持、异步复位 |
| rt_sequence | sequence_detector | 1001 序列、重叠检测、复位、固定随机序列 |
| rt_shift | right_shifter | 初值、移位方向、串行数据及边沿间保持 |
| rt_pipeline | multi_pipe_4bit | 两级流水、连续输入、复位、乘法及输出延迟 |

一轮固定 **140,430 次输出检查**。所有比较使用 `!==`，未知值不会被当成正确值；唯一 nonce 完成凭据及检查总数由固定 TB 生成。每题有一个故意错误实现，具体故障写入 manifest。一个 mutant 通过检出仅证明能识别该类错误，不能证明测试完备。

已确认的规格适配：

- RTLLM counter_12、sequence_detector 明确为异步低有效复位，与存档参考一致。sequence_detector 明确支持重叠，输出为消费最后一位后的 Moore 状态输出。
- multi_pipe_4bit 的参考实现只对 size=4 审计；本版本固定 size=4，不声称支持任意参数。两个寄存级对应输出在本次边沿后取前一边沿采样的乘积。
- right_shifter 保留原规格的 `initial q=0`。Yosys 能保留初始化属性，但这不证明 ASIC 上电值有保证。
- 将参考模块重命名成题目要求名称，去掉 timescale；不把参考 RTL 发送给生成模型。
- 本开发集限定单模块、单时钟/无时钟设计，暂未纳入异步 FIFO、复杂多模块和含不明确高阻语义的 ALU。选择先于模型生成，不按模型结果筛题。

`split-lock.json` 固定这 10 题属于 development。最终 40 题尚未选定/审计；相同 family 或近似变体不得进入 final（包括跨来源的计数器变体）。后续扩充 final 时仍须人工检查重复/相似关系，当前锁文件不是自动语义去重器。公开 benchmark 可能已进入模型训练数据，这个实验不能排除训练污染。

在仓库根目录重建及验证：

```bash
python3 build_dev.py
python3 batch.py init --run-dir runs/dev-audit --suite dev10 --rtl-dir benchmarks/dev10/reference --synthesis yosys
python3 batch.py run --run-dir runs/dev-audit --workers 4
python3 -m unittest -v test_dev
```

重建脚本仅依赖随库保存的上游快照，不需要联网；确定性重建由测试逐文件比对。修改规格、向量或适配时必须升级开发集版本并新建实验，不能继续已有模型实验。
