# 下一轮公开原题 RAG 对照：用户待审材料

状态：PREPARED_NOT_RELEASED。20候选静态核查后8题条件纳入、12题排除，拟96槽，全部NOT_STARTED。0模型、0编译/仿真/SAT/综合。无技术放行、无新生产账本。

A方法逐字复用：18段lowRISC库，原BM25/stopwords/top3/system/context。原A预算/选题文件仅历史保全，新范围及取消8192硬cap由protocol/overlay.json单独定义。旧240槽及服务错误不重跑，与旧240或三臂216提案不叠加。

元数据156题→63项历史/家族排除→剩余93题按原seed排序→只读首20题→8条件纳入。未补候选；不得根据检索或成绩换题。原文完整保存在B/originals，原始字节以文件为准，下文代码块只作展示。

所有题及参考来自NVlabs/verilog-eval固定commit c498220d0a52248f8e3fdffe279075215bde2da6，MIT原许可证见A/metadata/dataset-LICENSE。个别文件作者未建立；snapshot作者不是每个ref/test的作者。参考/test同库相关、非独立oracle；公开不等于训练未见，训练暴露UNKNOWN。

八题均为组合逻辑接口，含组合FSM转移，无寄存器时序题。不能用于声称中途复位、边沿间保持或握手事务收益。相关题组：019与087共享a&~b，114与106共享表查找形式；逐题报告，不冒称八个完全独立功能族。

原TB均在测试clk双边沿直接评分，wait_for_end_of_timestep仅定义；不宣称POST/NBA后统一采样。参考X会屏蔽比较：094边界两位为原题明示dont-care，和被排除084初始存储未定义不同。143题面允许multi-hot但原TB只测one-hot，覆盖缺口保留。

## 冻结时序

{
  "A": {
    "frozen_utc": "2026-10-24T03:04:59.341559+00:00",
    "a_lock_sha256": "c0609d940a0e586e2b7b5fc81ca6d58bd1eeee5e1d4cecbe40415317f341ead1",
    "protocol_lock_sha256": "63353db3ad1f7e297dff22faa2bb9de775b5cd7f67f8b20fcd275a9384d10f4e",
    "original_a_lock_sha256": "c0609d940a0e586e2b7b5fc81ca6d58bd1eeee5e1d4cecbe40415317f341ead1",
    "new_content_reads": 0,
    "candidate_ids": [
      "Prob145_circuit8",
      "Prob088_ece241_2014_q5b",
      "Prob122_kmap4",
      "Prob001_zero",
      "Prob155_lemmings4",
      "Prob019_m2014_q4f",
      "Prob151_review2015_fsm",
      "Prob094_gatesv",
      "Prob143_fsm_onehot",
      "Prob059_wire4",
      "Prob006_vectorr",
      "Prob052_gates100",
      "Prob111_fsm2s",
      "Prob114_bugs_case",
      "Prob084_ece241_2013_q12",
      "Prob087_gates",
      "Prob050_kmap1",
      "Prob101_circuit4",
      "Prob106_always_nolatches",
      "Prob154_fsm_ps2data"
    ]
  },
  "B": {
    "frozen_utc": "2026-10-24T03:09:56.628146+00:00",
    "b_lock_sha256": "659efea776676fb4a1983c5b65c0c7f9634624fae4ade13c7fae52160b7c9c9b",
    "a_lock_sha256": "c0609d940a0e586e2b7b5fc81ca6d58bd1eeee5e1d4cecbe40415317f341ead1",
    "protocol_lock_sha256": "63353db3ad1f7e297dff22faa2bb9de775b5cd7f67f8b20fcd275a9384d10f4e",
    "selected_ids": [
      "Prob001_zero",
      "Prob019_m2014_q4f",
      "Prob094_gatesv",
      "Prob143_fsm_onehot",
      "Prob114_bugs_case",
      "Prob087_gates",
      "Prob050_kmap1",
      "Prob106_always_nolatches"
    ],
    "retrieval_calls_so_far": 0
  },
  "C_start": {
    "utc": "2026-10-24T03:11:28.275347+00:00",
    "a_lock_sha256": "c0609d940a0e586e2b7b5fc81ca6d58bd1eeee5e1d4cecbe40415317f341ead1",
    "b_lock_sha256": "659efea776676fb4a1983c5b65c0c7f9634624fae4ade13c7fae52160b7c9c9b",
    "plan_lock_sha256": "e2ae89735e28be19525119598bf00d4391732bb2f942bc6b52eb84d4bc23eb29",
    "retrievals_before": 0
  }
}

## 全部候选分母

|序号|题目|决定|依据|
|---|---|---|---|

|1|Prob145_circuit8|排除|KEY_TIMING_UNRESOLVED：clock/a/p/q均1位；无复位、初态X。表中115ns时clock下降且a变0，而q变1；没有区分边沿前/后输入。参考q<=a、p高电平透明，不足以唯一解释原表同时变化。|

|2|Prob088_ece241_2014_q5b|排除|REFERENCE_STRUCTURE_CONFLICT：全1位，posedge、异步高复位A，A遇1转B，z由state/x决定。原题要求one-hot，参考reg state为单比特二进制A=0/B=1，不满足两状态one-hot结构。|

|3|Prob122_kmap4|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE：与历史parity8功能相同，仅宽度/表达形式改变；不是新独立奇偶测试。|

|4|Prob001_zero|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：仅1位zero，无输入、时钟、复位、有符号算术；始终为0，组合连续有效，不涉及初始化契约。|

|5|Prob155_lemmings4|排除|HISTORY_SUBSTANTIVE_OVERLAP：旧Prob127_lemmings1同一Lemmings左右行走/碰撞状态核心，且历史计数/状态扩展已暴露；保守排除，不把加dig/dead当全新独立题。|

|6|Prob019_m2014_q4f|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：in1/in2/out均1位，组合out=in1 AND NOT in2，无时钟复位或符号问题；文字完整描述bubble，无缺图。|

|7|Prob151_review2015_fsm|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE：旧Prob150_review2015_fsmonehot给出同一10状态图，另Prob095/096相关题已暴露；相同控制行为的组合/寄存器包装变化不成为独立新题。|

|8|Prob094_gatesv|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：in及三output均4位；out_both[2:0]相邻AND；out_any[3:1]相邻OR；out_different含3到0环绕XOR。out_both[3]/out_any[0]原题明确不关心；组合、无时钟复位、有符号运算。|

|9|Prob143_fsm_onehot|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：state[9:0]、next_state[9:0]及1位in/out1/out2；仅组合不含状态寄存器。完整图逐入边形成各next位，多有效state允许并存；输出按指定活跃状态并集，无时钟复位初态。|

|10|Prob059_wire4|排除|HISTORY_SUBSTANTIVE_OVERLAP：旧Prob032_vector0已为3位输入复制并拆到输出，本题仅改端口分组及复制次数，主要行为都是三输入无计算布线/扇出；保守近重复排除。|

|11|Prob006_vectorr|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE：旧Prob023_vector100r相同位序反转，仅100改8位，排除。|

|12|Prob052_gates100|排除|HISTORY_SUBSTANTIVE_OVERLAP：XOR规约与历史parity8宽度变体，OR规约与旧向量逻辑OR重叠；多输出打包未足以消除主体功能暴露，保守排除。|

|13|Prob111_fsm2s|排除|CLOCK_EDGE_UNSPECIFIED：clk/reset/j/k/out均1位；同步高复位OFF与状态图明确，但原文未指定有效时钟边沿；参考选择posedge，不能用参考补原题。|

|14|Prob114_bugs_case|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：code8位,out4位,valid1位；十个明确常量映射0..9，其他out=0且valid=0；纯组合全时有效，unsigned字面值，无时钟复位。|

|15|Prob084_ece241_2013_q12|排除|HISTORY_SUBSTANTIVE_OVERLAP：历史shiftreg8/rt_shift与mux8已有移位及索引选择主体组合，保守排除；不因加存储名义重标独立。|

|16|Prob087_gates|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：a,b及七outputs1位；AND/OR/XOR/NAND/NOR/XNOR/a&~b全部指定，组合连续有效，无符号/时钟/复位。|

|17|Prob050_kmap1|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：a,b,c/out均1位，完整8格图，除000外输出1；组合无时钟复位，输出连续有效，未声明4态输入真值。|

|18|Prob101_circuit4|排除|WITHIN_ROUND_FUNCTIONAL_NEAR_DUPLICATE：与本轮更早Prob050同为OR归约真值表，仅有效输入数/表示变化，保守排除后者；没有依据RAG表现选留。|

|19|Prob106_always_nolatches|条件纳入|CONDITIONAL_STATIC_ELIGIBLE：scancode16位，四1位方向输出；e06b/e072/e074/e075分别置对应位，其他全0；组合无时钟复位、全时有效。|

|20|Prob154_fsm_ps2data|排除|KEY_TIMING_UNRESOLVED：posedge同步reset；in8/out24/done1，first byte in[3]=1，done有效时三字节高到低。文字说第三字节后立即一周期，表在15/25/35边沿列2c/81/09却45才done；未定义表输入在边沿前还是后，参考按已采样输入转DONE。|


完整逐题契约/语言/初始化/接口/依赖/测试行号/作者来源/排除理由见 B/selection.json；全部原候选（包括排除题）保留60原文件及SHA/Git blob。

## 完整统一system（逐字复用，不向模型加入中文评语）

```text
Implement the given digital circuit in synthesizable SystemVerilog.
Return only one complete module in a single ```systemverilog code block.
Use exactly the specified module name and ports. Do not provide a testbench.
No includes, preprocessor directives, strings, hierarchical references, extra
modules, simulation system tasks, file IO, or attributes. Only $signed,
$unsigned and $clog2 system functions are permitted. Do not use delays.
The independent evaluator will supply all input stimuli and check outputs.
```

## 原始context-template

```text


<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
{fragments}
</generic_reference_context>

```

## Prob001_zero — 常零输出

条件纳入；独立正确性NOT_ESTABLISHED。未见相同常零任务；与NOT/门运算共有常量这一基本原语不单独判重复。

契约：仅1位zero，无输入、时钟、复位、有符号算术；始终为0，组合连续有效，不涉及初始化契约。

测试与局限：20个测试时钟双边沿观测，无输入空间；同源参考assign0，非独立oracle。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob001_zero_prompt.txt) SHA256 `1b79c7508ebf3f5d89aa3874b96be38eb6547a93a4400b3b984988564c85764c`；Git blob `8c1146c9dec8aeceb1c9c85d1c001b184115caf6`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob001_zero_ref.sv) SHA256 `7f4686eac875da1029bdaa5198b47a5390dc2def846cb58cad07907bd32f40f4`；Git blob `89ae9a8384e8c355d8fd45e1aa4ae4a9d14d3b8a`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob001_zero_test.sv) SHA256 `ebf2acb39a43d4ca53aa9c39c37941a61f288c8933e6eacf87b82ecc23cbd17c`；Git blob `fd4c826ec4d81c07d0083947a5387eac6edabc4e`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - output zero

The module should always outputs a LOW.


```

### 实际自动检索

{
  "task": "Prob001_zero",
  "selected_ids": [
    "LR002",
    "LR015",
    "LR003"
  ],
  "scores": [
    4.847378060351743,
    4.267503005426203,
    4.223343305172872
  ],
  "no_hit": false,
  "retrieval_seconds": 0.000371600006474182,
  "prompt_bytes": 211,
  "context_bytes": 1150
}

完整18段排名及逐词分数见 C/retrieval/Prob001_zero.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - output zero

The module should always outputs a LOW.



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR002; Delay Modeling; lines 1789-1790]
Synthesizable design modules must be designed around a zero-delay simulation
methodology. All forms of `#delay`, including `#0`, are not permitted.

[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.

[LR003; Sequential Logic (Latches); lines 1802-1803]
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob001_zero__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob019_m2014_q4f — 带反相输入的AND

条件纳入；独立正确性NOT_ESTABLISHED。旧Prob029是XNOR再XOR，旧Prob065是双四输入NAND；共有门原语但不是同一完整函数。与本批Prob087有共享输出，统计须标相关题组。

契约：in1/in2/out均1位，组合out=in1 AND NOT in2，无时钟复位或符号问题；文字完整描述bubble，无缺图。

测试与局限：100双边沿随机输入，非预声明穷举；评分看已稳定旧输入阶段，无统一postsettle保证。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob019_m2014_q4f_prompt.txt) SHA256 `97bd8fbb078bc6c1cddfb97a61f5a3e3ed8b33012333b295800d3cc6e1f0982e`；Git blob `8e49b0e833d9ac3360ced5152bf4fd27a5514291`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob019_m2014_q4f_ref.sv) SHA256 `c92c3177993007c8cb6d72fa96527a70431a66dc655c3b422bb94ed9c9ca9c29`；Git blob `dd455231e717dca3fee42a51e96ea9259cbe71cc`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob019_m2014_q4f_test.sv) SHA256 `084d74cb95eaa0adc2c33fa13fdb43a7bace3c5714bf98854a161f21d5812ea6`；Git blob `cd114078bc50d09ab601dd81aace9837301459ba`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in1
 - input  in2
 - output out

The module should implement the following circuit in Verilog. Two inputs
(in1 and in2) go to an AND gate, but the in2 input to the AND gate has a
bubble. The output of the AND gate is connected to 'out'.


```

### 实际自动检索

{
  "task": "Prob019_m2014_q4f",
  "selected_ids": [
    "LR018",
    "LR015",
    "LR003"
  ],
  "scores": [
    5.1954021019231345,
    3.404362645465794,
    2.969023870581372
  ],
  "no_hit": false,
  "retrieval_seconds": 0.0002626000059535727,
  "prompt_bytes": 402,
  "context_bytes": 1578
}

完整18段排名及逐词分数见 C/retrieval/Prob019_m2014_q4f.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in1
 - input  in2
 - output out

The module should implement the following circuit in Verilog. Two inputs
(in1 and in2) go to an AND gate, but the in2 input to the AND gate has a
bubble. The output of the AND gate is connected to 'out'.



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR018; Case Statements; lines 2245-2252]
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.

[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.

[LR003; Sequential Logic (Latches); lines 1802-1803]
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob019_m2014_q4f__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob094_gatesv — 相邻位关系与环绕差异

条件纳入；独立正确性NOT_ESTABLISHED。旧vectorgates直接对两输入向量做OR/NOT，无本题相邻索引与环绕关系；共享门原语，不是仅改位宽。

契约：in及三output均4位；out_both[2:0]相邻AND；out_any[3:1]相邻OR；out_different含3到0环绕XOR。out_both[3]/out_any[0]原题明确不关心；组合、无时钟复位、有符号运算。

测试与局限：定向3/6/12/9/5加双边沿随机；参考将两无效边界位设X，TB屏蔽这些位，不能声称所有12位均受约束。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob094_gatesv_prompt.txt) SHA256 `6e699bd5c4e6b9fb053576134ae006118f0b94d9b997cbd46aade8e72318dd83`；Git blob `fdde05a49134cb33f60cdae088ead77367b42232`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob094_gatesv_ref.sv) SHA256 `5a9bf7d169021df9c52559b115ec3aa89d26f68c3beefa85ed8f0b7a2b01cb0f`；Git blob `532fc4fc866c1a21b1e5adcd228d66490383bfd4`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob094_gatesv_test.sv) SHA256 `cdd60ca258c7f1ba120a97731b86c7a34582cb596a36ee2449af9e316478e592`；Git blob `6f72e58848028cdae5ee2c08cb4df041597dd1c0`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in            (4 bits)
 - output out_both      (4 bits)
 - output out_any       (4 bits)
 - output out_different (4 bits)

You are given a four-bit input vector. We want to know some relationships
between each bit and its neighbour:

  (1) out_both: Each bit of this output vector should indicate whether
  both the corresponding input bit and its neighbour to the left (higher
  index) are '1'. For example, out_both[2] should indicate if in[2] and
  in[3] are both 1. Since in[3] has no neighbour to the left, the answer
  is obvious so we don't need to know out_both[3].

  (2) out_any: Each bit of this output vector should indicate whether any
  of the corresponding input bit and its neighbour to the right are '1'.
  For example, out_any[2] should indicate if either in[2] or in[1] are 1.
  Since in[0] has no neighbour to the right, the answer is obvious so we
  don't need to know out_any[0].

  (3) out_different: Each bit of this output vector should indicate
  whether the corresponding input bit is different from its neighbour to
  the left. For example, out_different[2] should indicate if in[2] is
  different from in[3]. For this part, treat the vector as wrapping
  around, so in[3]'s neighbour to the left is in[0].


```

### 实际自动检索

{
  "task": "Prob094_gatesv",
  "selected_ids": [
    "LR015",
    "LR018",
    "LR002"
  ],
  "scores": [
    10.99443971766194,
    8.651627957138844,
    4.847378060351743
  ],
  "no_hit": false,
  "retrieval_seconds": 0.0004054000019095838,
  "prompt_bytes": 1400,
  "context_bytes": 1576
}

完整18段排名及逐词分数见 C/retrieval/Prob094_gatesv.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in            (4 bits)
 - output out_both      (4 bits)
 - output out_any       (4 bits)
 - output out_different (4 bits)

You are given a four-bit input vector. We want to know some relationships
between each bit and its neighbour:

  (1) out_both: Each bit of this output vector should indicate whether
  both the corresponding input bit and its neighbour to the left (higher
  index) are '1'. For example, out_both[2] should indicate if in[2] and
  in[3] are both 1. Since in[3] has no neighbour to the left, the answer
  is obvious so we don't need to know out_both[3].

  (2) out_any: Each bit of this output vector should indicate whether any
  of the corresponding input bit and its neighbour to the right are '1'.
  For example, out_any[2] should indicate if either in[2] or in[1] are 1.
  Since in[0] has no neighbour to the right, the answer is obvious so we
  don't need to know out_any[0].

  (3) out_different: Each bit of this output vector should indicate
  whether the corresponding input bit is different from its neighbour to
  the left. For example, out_different[2] should indicate if in[2] is
  different from in[3]. For this part, treat the vector as wrapping
  around, so in[3]'s neighbour to the left is in[0].



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.

[LR018; Case Statements; lines 2245-2252]
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.

[LR002; Delay Modeling; lines 1789-1790]
Synthesizable design modules must be designed around a zero-delay simulation
methodology. All forms of `#delay`, including `#0`, are not permitted.
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob094_gatesv__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob143_fsm_onehot — 十状态组合转移逻辑

条件纳入；独立正确性NOT_ESTABLISHED。旧Prob150虽也10状态one-hot，但图为1101计时器，本题为连续1长度分支图，端口/转移/输出行为实质不同；FSM表达原语共享单列。

契约：state[9:0]、next_state[9:0]及1位in/out1/out2；仅组合不含状态寄存器。完整图逐入边形成各next位，多有效state允许并存；输出按指定活跃状态并集，无时钟复位初态。

测试与局限：原TB先遍历10状态×2输入，再200随机one-hot；未覆盖题中允许的多hot组合，0态阶段in未初始化。多hot正确性待独立验证，不能以原TB通过证明。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob143_fsm_onehot_prompt.txt) SHA256 `e33a1e959db7f84d591c7fbe933b1ee8d2212f9bdbc229658c764c08dfcdf67b`；Git blob `513d06130acfc045dca0571d9a55e323e388661c`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob143_fsm_onehot_ref.sv) SHA256 `713dafd41effad29c326f7e3592115be3394a9de809f5849cbe349add87219f1`；Git blob `5de4e474293820554aa25d632327142add5e122f`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob143_fsm_onehot_test.sv) SHA256 `b3f86936ea281b3a5e95e4fefdd2354b27fb5b3472b4207ef592555fc861cbba`；Git blob `eb8120885514e5981261c8e72011d9a158375cbc`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in
 - input  state (10 bits)
 - output next_state (10 bits)
 - output out1
 - output out2

Given the follow state machine with 1 input and 2 outputs (the outputs
are given as "(out1, out2)"):

  S0 (0, 0) --0--> S0
  S0 (0, 0) --1--> S1
  S1 (0, 0) --0--> S0
  S1 (0, 0) --1--> S2
  S2 (0, 0) --0--> S0
  S2 (0, 0) --1--> S3
  S3 (0, 0) --0--> S0
  S3 (0, 0) --1--> S4
  S4 (0, 0) --0--> S0
  S4 (0, 0) --1--> S5
  S5 (0, 0) --0--> S8
  S5 (0, 0) --1--> S6
  S6 (0, 0) --0--> S9
  S6 (0, 0) --1--> S7
  S7 (0, 1) --0--> S0
  S7 (0, 1) --1--> S7
  S8 (1, 0) --0--> S0
  S8 (1, 0) --1--> S1
  S9 (1, 1) --0--> S0
  S9 (1, 1) --1--> S1

Suppose this state machine uses one-hot encoding, where state[0] through
state[9] correspond to the states S0 though S9, respectively. The outputs
are zero unless otherwise specified. The next_state[0] through next_state[9] 
correspond to the transition to next states S0 though S9. For example, The 
next_state[1] is set to 1 when the next state is S1 , otherwise, it is set to 0.

Here, the input state[9:0] can be a combinational of multiple states, and 
the TopModule is expected to response.
For example: 
When the state[9:0] = 10'b0000010100, state[4] == 1, and state[2] == 1, the 
states includes S4, and S2 states.

The module should implement the state transition logic and output logic
portions of the state machine (but not the state flip-flops). You are
given the current state in state[9:0] and must implement next_state[9:0] 
and the two outputs.


```

### 实际自动检索

{
  "task": "Prob143_fsm_onehot",
  "selected_ids": [
    "LR006",
    "LR010",
    "LR018"
  ],
  "scores": [
    8.66233512422528,
    5.425544321663798,
    5.1954021019231345
  ],
  "no_hit": false,
  "retrieval_seconds": 0.0003423000016482547,
  "prompt_bytes": 1660,
  "context_bytes": 1403
}

完整18段排名及逐词分数见 C/retrieval/Prob143_fsm_onehot.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in
 - input  state (10 bits)
 - output next_state (10 bits)
 - output out1
 - output out2

Given the follow state machine with 1 input and 2 outputs (the outputs
are given as "(out1, out2)"):

  S0 (0, 0) --0--> S0
  S0 (0, 0) --1--> S1
  S1 (0, 0) --0--> S0
  S1 (0, 0) --1--> S2
  S2 (0, 0) --0--> S0
  S2 (0, 0) --1--> S3
  S3 (0, 0) --0--> S0
  S3 (0, 0) --1--> S4
  S4 (0, 0) --0--> S0
  S4 (0, 0) --1--> S5
  S5 (0, 0) --0--> S8
  S5 (0, 0) --1--> S6
  S6 (0, 0) --0--> S9
  S6 (0, 0) --1--> S7
  S7 (0, 1) --0--> S0
  S7 (0, 1) --1--> S7
  S8 (1, 0) --0--> S0
  S8 (1, 0) --1--> S1
  S9 (1, 1) --0--> S0
  S9 (1, 1) --1--> S1

Suppose this state machine uses one-hot encoding, where state[0] through
state[9] correspond to the states S0 though S9, respectively. The outputs
are zero unless otherwise specified. The next_state[0] through next_state[9] 
correspond to the transition to next states S0 though S9. For example, The 
next_state[1] is set to 1 when the next state is S1 , otherwise, it is set to 0.

Here, the input state[9:0] can be a combinational of multiple states, and 
the TopModule is expected to response.
For example: 
When the state[9:0] = 10'b0000010100, state[4] == 1, and state[2] == 1, the 
states includes S4, and S2 states.

The module should implement the state transition logic and output logic
portions of the state machine (but not the state flip-flops). You are
given the current state in state[9:0] and must implement next_state[9:0] 
and the two outputs.



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR006; Sequential Logic (Registers); lines 1818-1820]
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.

[LR010; Combinational Logic; lines 2152-2153]
Do not use three-state logic (`Z` state) to accomplish on-chip logic such as
muxing.

[LR018; Case Statements; lines 2245-2252]
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob143_fsm_onehot__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob114_bugs_case — 数字键扫描码映射

条件纳入；独立正确性NOT_ESTABLISHED。历史decoder3为索引one-hot译码，本题为稀疏非连续scancode到数字映射，非宽度或重命名变体；与本批箭头scancode为相关表驱动题组。

契约：code8位,out4位,valid1位；十个明确常量映射0..9，其他out=0且valid=0；纯组合全时有效，unsigned字面值，无时钟复位。

测试与局限：列举十码及若干无效码+1000随机，非保证全256遍历；参考default valid0/out预置0，没有latch。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob114_bugs_case_prompt.txt) SHA256 `8c995017a12715c1f9a1945e73db92bee1d893a2a74f49f10d0bffc5cfb36a0e`；Git blob `ebb9a1922c721683f8635e680cd696c40787e35a`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob114_bugs_case_ref.sv) SHA256 `97aaf43498481511ccc8ca815b33703d0e9a41a732cd36af420cd26083b4db4e`；Git blob `b79e7b6e5d9f16c435eaa97b1bebf28219e938dc`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob114_bugs_case_test.sv) SHA256 `2d7330963dd2ab318d26013a3ca1b035fcdc8dd53ae687a685322183b565ffda`；Git blob `bad8eddad50204eb00f787a14440f05be3d56678`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  code (8 bits)
 - output out  (4 bits)
 - output valid

The module should recognize 8-bit keyboard scancodes for keys 0 through
9. It should indicate whether one of the 10 cases were recognized
(valid), and if so, which key was detected. If the 8-bit input is 8'h45,
8'h16, 8'h1e, 8'h26, 8'h25, 8'h2e, 8'h36, 8'h3d, 8'h3e, or 8'h46, the
4-bit output will be set to 0, 1, 2, 3, 4, 5, 6, 7, 8, or 9 respectively,
the 1-bit valid would be set to 1. If the input does not match any of the
cases, both output signals would be set to 0.


```

### 实际自动检索

{
  "task": "Prob114_bugs_case",
  "selected_ids": [
    "LR015",
    "LR018",
    "LR003"
  ],
  "scores": [
    13.16417774531334,
    9.50341036696501,
    4.418692918927001
  ],
  "no_hit": false,
  "retrieval_seconds": 0.0002925000007962808,
  "prompt_bytes": 695,
  "context_bytes": 1578
}

完整18段排名及逐词分数见 C/retrieval/Prob114_bugs_case.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  code (8 bits)
 - output out  (4 bits)
 - output valid

The module should recognize 8-bit keyboard scancodes for keys 0 through
9. It should indicate whether one of the 10 cases were recognized
(valid), and if so, which key was detected. If the 8-bit input is 8'h45,
8'h16, 8'h1e, 8'h26, 8'h25, 8'h2e, 8'h36, 8'h3d, 8'h3e, or 8'h46, the
4-bit output will be set to 0, 1, 2, 3, 4, 5, 6, 7, 8, or 9 respectively,
the 1-bit valid would be set to 1. If the input does not match any of the
cases, both output signals would be set to 0.



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.

[LR018; Case Statements; lines 2245-2252]
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.

[LR003; Sequential Logic (Latches); lines 1802-1803]
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob114_bugs_case__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob087_gates — 七种二输入逻辑门

条件纳入；独立正确性NOT_ESTABLISHED。共享旧门原语但七函数接口未发现完整历史同题；与本批Prob019共享一个输出，须报告相关性，不能当完全独立题族。

契约：a,b及七outputs1位；AND/OR/XOR/NAND/NOR/XNOR/a&~b全部指定，组合连续有效，无符号/时钟/复位。

测试与局限：列举00/01/10/11后200随机；参考各连续assign；初始未驱动阶段可X屏蔽。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob087_gates_prompt.txt) SHA256 `db35b613e2e9800fd53faf14c717fc053fa723f4a97a7eecfbc459f18fa54f9d`；Git blob `168281dce075a9876488ec7d870c3e3b162c74ca`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob087_gates_ref.sv) SHA256 `fd05947bb790cc30fbc348bd272053377e718611affdd86892a1922edec454f2`；Git blob `635b2fa8f2ac4b09262a930920ad51a0b0ab5fe5`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob087_gates_test.sv) SHA256 `cf35d2299705395fa53f59d3f1a18f8de39bb6dadbdac6bdc55a221d7883e8a7`；Git blob `0ddee2f713a7063e88b59916d535096cc6af8740`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - output out_and
 - output out_or
 - output out_xor
 - output out_nand
 - output out_nor
 - output out_xnor
 - output out_anotb

The module should implement a combinational circuit with two inputs, a
and b. There are 7 outputs, each with a logic gate driving it:

  (1) out_and: a and b
  (2) out_or: a or b
  (3) out_xor: a xor b
  (4) out_nand: a nand b
  (5) out_nor: a nor b
  (6) out_xnor: a xnor b
  (7) out_anotb: a and-not b


```

### 实际自动检索

{
  "task": "Prob087_gates",
  "selected_ids": [
    "LR018",
    "LR003",
    "LR015"
  ],
  "scores": [
    5.1954021019231345,
    3.662540400024308,
    3.404362645465794
  ],
  "no_hit": false,
  "retrieval_seconds": 0.00035509999725036323,
  "prompt_bytes": 613,
  "context_bytes": 1578
}

完整18段排名及逐词分数见 C/retrieval/Prob087_gates.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - output out_and
 - output out_or
 - output out_xor
 - output out_nand
 - output out_nor
 - output out_xnor
 - output out_anotb

The module should implement a combinational circuit with two inputs, a
and b. There are 7 outputs, each with a logic gate driving it:

  (1) out_and: a and b
  (2) out_or: a or b
  (3) out_xor: a xor b
  (4) out_nand: a nand b
  (5) out_nor: a nor b
  (6) out_xnor: a xnor b
  (7) out_anotb: a and-not b



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR018; Case Statements; lines 2245-2252]
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.

[LR003; Sequential Logic (Latches); lines 1802-1803]
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).

[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob087_gates__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob050_kmap1 — 三输入卡诺图

条件纳入；独立正确性NOT_ESTABLISHED。与旧多输出向量门共有OR基本原语；本题完整单输出真值表不同，无同题宽度替换证据。后续Prob101属同轮OR近重复，后者排除。

契约：a,b,c/out均1位，完整8格图，除000外输出1；组合无时钟复位，输出连续有效，未声明4态输入真值。

测试与局限：10递增输入覆盖3位0..7并回绕，加200随机；参考a|b|c。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob050_kmap1_prompt.txt) SHA256 `e32c77b94e20cf4bba3c5e32d8ef2c95406b84bc3c46679f93061b1ebcdde4b6`；Git blob `97c5130dbc2d4fcf846cc3c07e09f4cac76b8b39`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob050_kmap1_ref.sv) SHA256 `d8f2229363c7ae8748c8d9b2efb025bd5eb297f5aa9bb49a30dea271f68e8b2b`；Git blob `1443de47e0579d2f09c31a5e7b2ad27fe9f845a0`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob050_kmap1_test.sv) SHA256 `269dd594ea2d6c7f39136c599ea7c48637e34f0a02b19dc585b136d80b969e1f`；Git blob `e903dce0435d476d1db1a2aece6309de54e93daf`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - input  c
 - output out

The module should implement the circuit described by the Karnaugh map
below.

          a
   bc   0   1
   00 | 0 | 1 |
   01 | 1 | 1 |
   11 | 1 | 1 |
   10 | 1 | 1 |


```

### 实际自动检索

{
  "task": "Prob050_kmap1",
  "selected_ids": [
    "LR018",
    "LR015",
    "LR003"
  ],
  "scores": [
    3.7475288712241452,
    3.404362645465794,
    2.969023870581372
  ],
  "no_hit": false,
  "retrieval_seconds": 0.00042379999649710953,
  "prompt_bytes": 374,
  "context_bytes": 1578
}

完整18段排名及逐词分数见 C/retrieval/Prob050_kmap1.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - input  c
 - output out

The module should implement the circuit described by the Karnaugh map
below.

          a
   bc   0   1
   00 | 0 | 1 |
   01 | 1 | 1 |
   11 | 1 | 1 |
   10 | 1 | 1 |



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR018; Case Statements; lines 2245-2252]
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.

[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.

[LR003; Sequential Logic (Latches); lines 1802-1803]
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob050_kmap1__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## Prob106_always_nolatches — 箭头扫描码识别

条件纳入；独立正确性NOT_ESTABLISHED。与历史一般decoder只有表查找原语共享；本轮Prob114为数字输出稀疏表，本题为方向one-hot输出，保留相关表驱动题组标记，不声称完全独立族。

契约：scancode16位，四1位方向输出；e06b/e072/e074/e075分别置对应位，其他全0；组合无时钟复位、全时有效。

测试与局限：定向有效/相邻无效码与30000随机；不等于穷尽65536，参考每次输出全0再case。

原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob106_always_nolatches_prompt.txt) SHA256 `bca22f47f123f3faafed3372bcec4a5b76e84327375f34464b75746479ac22d6`；Git blob `a96afaade60ad596b016fb17026008f07181cadb`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob106_always_nolatches_ref.sv) SHA256 `c224ca40684f97dd739096b361e1d85155a07ae5faf9548c12575d6f0f347ad6`；Git blob `d6f194d7e1c3a4539713e3b44acc774f52b2f711`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob106_always_nolatches_test.sv) SHA256 `fd636060098952703ed11e5d88b56f384a91c0a573d10ed98187db89cdf62136`；Git blob `56bbbf28ed89e89290d5146851a937fa49dac538`

### 完整原题 / no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  scancode (16 bits)
 - output left
 - output down
 - output right
 - output up

The module should process scancodes from a PS/2 keyboard for a game.
Given the last two bytes of scancodes received, you need to indicate
whether one of the arrow keys on the keyboard have been pressed. This
involves a fairly simple mapping, which can be implemented as a case
statement (or if-elseif) with four cases.

  Scancode[15:0] | Arrow key
  16'he06b       | left arrow
  16'he072       | down arrow
  16'he074       | right arrow
  16'he075       | up arrow
  Anything else  | none

Your circuit has one 16-bit input, and four outputs. Build this circuit
that recognizes these four scancodes and asserts the correct output.


```

### 实际自动检索

{
  "task": "Prob106_always_nolatches",
  "selected_ids": [
    "LR015",
    "LR013",
    "LR014"
  ],
  "scores": [
    9.836234700127847,
    6.427679002525393,
    6.325150536690643
  ],
  "no_hit": false,
  "retrieval_seconds": 0.0004499000060604885,
  "prompt_bytes": 878,
  "context_bytes": 1348
}

完整18段排名及逐词分数见 C/retrieval/Prob106_always_nolatches.json；未人工替换。

### 完整 rag user（原题+原模板+原片段）

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  scancode (16 bits)
 - output left
 - output down
 - output right
 - output up

The module should process scancodes from a PS/2 keyboard for a game.
Given the last two bytes of scancodes received, you need to indicate
whether one of the arrow keys on the keyboard have been pressed. This
involves a fairly simple mapping, which can be implemented as a case
statement (or if-elseif) with four cases.

  Scancode[15:0] | Arrow key
  16'he06b       | left arrow
  16'he072       | down arrow
  16'he074       | right arrow
  16'he075       | up arrow
  Anything else  | none

Your circuit has one 16-bit input, and four outputs. Build this circuit
that recognizes these four scancodes and asserts the correct output.



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified selected prose.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[LR015; Case Statements; lines 2189-2192]
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.

[LR013; Case Statements; lines 2163-2164]
Never use either the `full_case` or `parallel_case` pragmas. These pragmas can
easily cause simulation/synthesis mismatches.

[LR014; Case Statements; lines 2181-2185]
The `unique` prefix is recommended before all case statements, as it creates
simulation assertions that can catch certain mistakes. In some cases, `priority`
may be used instead of `unique`, though in such cases, cascaded ternary
structures should be the preferred way of representing priority encoders as
they are a more readable representation for priority encoders.
</generic_reference_context>

```

两条件共享上述统一system；完整发送JSON为C/requests/Prob106_always_nolatches__{condition}__{model}__s00{sample}.json；不包含ref/test或本文件中文解释。

## 预算、停止与待审边界

8题×3指定模型×有/无RAG×2样本=96调用机会，全部NOT_STARTED。每次只生成RTL，无IR/反馈/补样。固定题序、条件序、模型序、样本序；并发1、单请求180秒，无8192输出硬cap，无整批墙时上限；保留HTTP1MiB/文本128KiB及后续执行器磁盘保护。实际input/output/reasoning/cache与费用如实记录，缺失null，不把无cap解释成无限资源。

预约消耗机会；首次HTTP服务错/transport/UNKNOWN/模型provider不匹配/哈希或资源异常即停，不自动retry/fallback/续写/补样/扩批。不得新建接入探针；本轮只复用已审OpenRouter路线配置，不访问账户或模型。

当前仅构造拟发送完整请求，未实际发送，也未证明服务端无内部包装/重试。旧direct-api-v1硬绑定旧20题，不可将本包直接交旧入口执行；将来新批映射、工具兼容校准、独立判据、生产账本/技术放行必须另行审核，不能复用旧账本或旧放行。

额外独立验证见independent-validation-proposal.json：仅具体候选计划和待审真值表达，没有运行。审阅者已见参考，故本草案不冒充独立oracle；需独立人员按原题复核。原题、测试与参考始终不改。

冻结后停止。由总控独立核查并呈用户审核；本材料不授权模型运行、方法调优或下一轮筛选。
