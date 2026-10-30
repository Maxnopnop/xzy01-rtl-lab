# 供总控核验后呈用户：公开入选题原文

最新补充：总控独立对照已定位编译环境问题，原文件仅恢复COMSPEC后编译成功，尚无仿真。原失败保留；以[总控诊断补充](COORDINATOR_ADDENDUM.md)更新下文先前UNKNOWN结论。先总控核验，再由用户确认选题和方案，不自动执行。

2026-10-16。目标5题，按预声明规则审查19题后仅条件选入2题，缺3题，未补样或放宽标准。下列中文说明不是模型prompt；每个原文块来自保存的上游原始文件，未经改写。实际system/输出包装另列为项目编写。模型调用0；先总控核验，再由用户确认选题和方案，未确认前不执行。

完整分母和17项未选理由见selection.json。原始数据包public-originals.zip含公开参考和TB，仅供审阅/评测，不可整包交生成模型。

## 1. Prob018_mux256to1

中文题意：从256位输入向量中，用8位sel选择一个bit输出。

入选理由及历史接触：接口及索引关系明确；与旧两路mux相比增加了完整索引选择契约。但仍属同一mux大类，不能标成模型未见或完全独立新机制。

测试与参考局限：原test/ref文件齐全。测试随机产生输入和sel，不等于全部输入覆盖；第一次参考别名编译失败，尚无成功仿真。组合电路无复位或边沿契约，复位增强项N/A。

官方来源：[NVlabs/verilog-eval 原文件](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob018_mux256to1_prompt.txt)；[本地原文](E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261016/public-benchmark-rag-v1/upstream/dataset_spec-to-rtl/Prob018_mux256to1_prompt.txt)。

固定commit：`c498220d0a52248f8e3fdffe279075215bde2da6`；许可：MIT；单题作者未核实（数据集版权为NVIDIA Research Projects）。

原prompt SHA256：`60e907332df45bd577d462dc0f8043139dbd5484af7e6bd36d4e8ec621a851b2`。

原文开始（不含下方中文解释或本地格式包装）：

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in  (256 bits)
 - input  sel (  8 bits)
 - output out

The module should implement a 1-bit wide, 256-to-1 multiplexer. The 256
inputs are all packed into a single 256-bit input vector. sel=0 should
select in[0], sel=1 selects bits in[1], sel=2 selects bits in[2], etc.

```

## 2. Prob095_review2015_fsmshift

中文题意：同步高有效复位后使能输出保持四个周期，然后保持关闭，直到再次复位。

入选理由及历史接触：与旧周期分频和按输入触发的请求延迟不同，适合关注四周期边界和终态保持；FSM/计数器基础构件曾接触，不能当作私有holdout。

测试与参考局限：原test/ref文件齐全。原刺激仅在负沿随机改变reset，初始未知参考位通配；不能宣称覆盖任意中途复位相位。第二题校准因前题失败停止而未运行，参考独立性未建立。

官方来源：[NVlabs/verilog-eval 原文件](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob095_review2015_fsmshift_prompt.txt)；[本地原文](E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261016/public-benchmark-rag-v1/upstream/dataset_spec-to-rtl/Prob095_review2015_fsmshift_prompt.txt)。

固定commit：`c498220d0a52248f8e3fdffe279075215bde2da6`；许可：MIT；单题作者未核实（数据集版权为NVIDIA Research Projects）。

原prompt SHA256：`31a48288034070f7ab847da07c03fcbfcd2cc973fed3b0f2da5c68d1fed349b0`。

原文开始（不含下方中文解释或本地格式包装）：

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - output shift_ena

This module is a part of the FSM for controlling a shift register, we
want the ability to enable the shift register for exactly 4 clock cycles
whenever the proper bit pattern is detected. Whenever the FSM is reset,
assert shift_ena for 4 cycles, then 0 forever (until reset). Reset should
be active high synchronous.

Assume all sequential logic is triggered on the positive edge of the
clock.

```

## 项目编写的统一包装（不属于上游原题）

完整文件见project-wrapper/system.txt；有RAG时仅追加project-wrapper中的固定通用参考容器。三模型同题同条件拟发送消息完全一致，服务端隐藏包装及共同硬输出预算尚未验证。原题不追加任何复位、时序、测试示例或答案说明。

## 缺额说明

算术类：历史原题或位宽近重复。寄存器类：存在端口冲突、未声明初始化或DFF近重复。计数器类：历史模数/偏移变体。完整排除理由和同类名额未选项见selection.json。当前两题都仅为条件入选，不代表工具验证、独立参考或执行就绪。
