# 独立通用文档 RAG：用户审核包

交付核查：audit.json 的22项结构/来源/字节检查通过；7项通用fixture检查另见generic-check.json。只读重算历史四包共2647项文件哈希均匹配；范围及路径见audit.json preservation。此检查不是独立审核结论，也不是RTL正确性测试。完整封包锁为packet-lock.json，锁的摘要见delivery.json。

状态 PREPARED_NOT_RELEASED。20个新候选静态核查，2题条件纳入、18题排除；24个拟调用槽全部NOT_STARTED。0模型/embedding/rerank/编译/仿真/SAT/综合；未创建生产账本或technical-release。未补足8题，未扩候选。

## 方法依据与隔离边界

A在读取新候选前封存：完整lowRISC Verilog Coding Style Guide，commit 9c15ff5dce23eef969e00ab3715153967419eadd，CC-BY-4.0，lowRISC contributors。使用缓存完整原文而非旧精选片段；1来源、48段，逐行贪心<=2048字符、全覆盖无筛主题，可重构原文件。切分可能跨Markdown围栏，不修整。来源/许可SHA见A/source-manifest.json，完整原文/许可证见A/sources。它是风格指南而非语言标准。

检索为新stdlib TF-IDF cosine：(1+ln tf)×(ln((1+N)/(1+df))+1)，L2；token规则[a-z_][a-z0-9_]*、lower；无stopwords/stemming/同义词/扩写，top3正分，平分按ID，无命中为空。算法一般依据 https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting 。所有数值参数在新题读取前冻结。未使用旧错误/成绩/题目/检索结果调整方法。7项通用词fixture通过，只是软件检查。

当前agent已有历史题目和结果的认知暴露，不能声称认知盲法。时间隔离可核验，不能证明彻底消除认知影响；历史文件此次仅用于排除及不变baseline。公开题训练暴露UNKNOWN。baseline中历史措辞independent evaluator不是独立性证明。指南通用例子可能不符合任务允许构造，原题与system约束优先。

## 来源、候选与参考局限

NVlabs/verilog-eval固定commit c498220d0a52248f8e3fdffe279075215bde2da6，MIT，许可证在A/metadata/dataset-LICENSE。156元数据题→83历史/家族排除→73剩余按冻结seed哈希排序→仅首20。60次原始文件GET，60文件93545字节，0重试；没有额外候选。全部原文件、Git blob、SHA和URL见B/access.json。个别prompt/ref/TB作者未建立；commit作者不代替文件作者。参考与TB同源相关，没有独立oracle或正确性签核。

所有20个原TB的wait_for_end_of_timestep只有定义，计分位于测试clk双边沿active区，不能称统一POST/NBA后采样；参考X会屏蔽比较。此次只有静态核查，工具兼容、调度/边界语义及覆盖均未运行验证。不将条件纳入写成PASS。

## 全部新候选决定

|rank|候选|决定|理由|
|---|---|---|---|

|1|Prob055_conditional|条件纳入|CONDITIONAL_STATIC_ELIGIBLE；a/b/c/d及min均8位；纯组合unsigned min(a,b,c,d)，相等时值相同，无优先输出索引、时钟或初始化要求。参考从a开始依次比较b/c/d。 历史rt_comparator是两数大小/相等标志；本题四操作数归约选择数值，非仅位宽替换；共享比较/选择原语明确保留为相关性。未发现同一完整min4行为。|

|2|Prob142_lemmings2|排除|HISTORY_SUBSTANTIVE_OVERLAP；全1位，posedge异步高复位walk_left；ground=0坠落并保持原方向，落地恢复，坠落时碰撞不转向。参考四状态。 已读Prob127_lemmings1及Prob155_lemmings4，后者包含同一行走/坠落子行为。|

|3|Prob124_rule110|条件纳入|CONDITIONAL_STATIC_ELIGIBLE；clk/load1位，data/q512位；posedge，load优先同步装载；无复位，首次load前未定义。原8行局部真值完整，左右越界为0。参考零条件111、000、100与原表一致；511位右移切片在512位按位表达式上下文中零扩展，边界语义需未来工具验证，未编译。 历史移位器和相邻门题共享索引/邻居原语，但没有此512单元非线性局部规则迭代状态演化；不以共享基础语法本身排除。|

|4|Prob016_m2014_q4j|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE；x/y4位，sum5位；无符号组合加法，题要求full adders，参考直接加法，结构不由TB验证。 历史adder8/加减法题同一加法，仅宽度改变。|

|5|Prob135_m2014_q6b|排除|KEY_CONTRACT_AMBIGUITY；y3/w1/Y1；无clk，要求just next-state logic for y[1]，末句又称Y1 is y[1]，当前位与次态位措辞冲突；参考选择次态，不据参考补题。 与本轮后续138为输入0/1对调后的相同六状态图；本题先因关键契约歧义排除。|

|6|Prob026_alwaysblock1|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE；a/b及两个输出1位，组合AND，分别assign和always；无时钟复位。 历史Prob087_gates包含同一AND，复制输出/语法要求不构成新功能。|

|7|Prob139_2013_q2bfsm|排除|HISTORY_SUBSTANTIVE_OVERLAP；posedge同步低复位；复位释放首周期f=1，随后检测101，g置1并等待两周期内y决定永久保持或清零至reset。参考以G1/G2和P0/P1表达。 历史sequence101已暴露相同触发序列，外加两周期确认和锁存控制；保守判主体序列检测重叠，不据扩展宣称独立新题。|

|8|Prob020_mt2015_eq2|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE；A/B2位z1位，组合A==B，二值域、无时钟复位。 已读rt_comparator三位A_equal同一功能，位宽改变和删除其他输出。|

|9|Prob112_always_case2|排除|HISTORY_SUBSTANTIVE_OVERLAP；in4,pos2；最低置位索引，零输入pos=0，无时钟复位。原例用8位仅说明规则，接口明确4位。 历史encoder4为高位优先；改变优先方向并去掉valid仍属同一优先编码主体，保守排除。|

|10|Prob010_mt2015_q4a|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE；x/y/z1位；组合(x^y)&x，在二值域等于x&~y。 与已读Prob019_m2014_q4f及Prob087 out_anotb相同完整函数。|

|11|Prob108_rule90|排除|WITHIN_ROUND_SUBSTANTIVE_OVERLAP；posedge、同步load、data/q512位；邻居XOR、越界0，无reset。参考右移切片与左移拼接XOR。 更早条件纳入124具有相同512单元接口/加载/边界/迭代结构；替换局部规则的同族近重复保守排除，不按检索选择。|

|12|Prob140_fsm_hdlc|排除|HISTORY_SUBSTANTIVE_OVERLAP；全1位；posedge同步高复位到前一位0，5个1后0为disc、6后0为flag、至少7为err，Moore整周期。参考十状态。 已读Prob143_fsm_onehot为同一十状态转移图；S8=discard、S9=flag、S7=error，编码输出与加状态寄存器不消除图的实质暴露。|

|13|Prob137_fsm_serial|排除|HISTORY_SUBSTANTIVE_OVERLAP；全1位，posedge同步高reset；0起始8数据1停止，无正确停止则等待1后重启。参考done为DONE状态一周期。 历史Prob146_fsm_serialdata包含同一起始/8数据/停止/错误恢复，删除数据输出为子任务。|

|14|Prob129_ece241_2013_q8|排除|HISTORY_SUBSTANTIVE_OVERLAP；全1位，posedge，低有效异步复位；三状态Mealy，S10时z=x。 历史sequence101相同重叠101识别，改复位极性/Mealy采样是变体，不能当独立新序列。|

|15|Prob153_gshare|排除|KEY_RESET_CONTRACT_MISSING；7位pc/history与128项2位饱和计数器，posedge异步高reset；训练误预测优先恢复历史，同项预测读更新前值。原文未给reset后的PHT计数器值及history值；参考选LNT=1和0，不能用参考补齐。提及的时序图未附，但文字已给读写先后。 不因复杂度或预期难度排除；决定性问题是复位值缺失。|

|16|Prob048_m2014_q4c|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE；clk/d/r/q1位，active-high同步清0；原文未明确有效边沿，参考选posedge。 历史dff/dff8r同一功能的位宽/端口变体；另保留边沿未明示问题。|

|17|Prob116_m2014_q3|排除|KEY_INDEX_CONTRACT_AMBIGUITY；x4位f1位，表列x[1]x[2]、行x[3]x[4]；接口未规定[4:1]还是[3:0]映射，参考选[3:0]及特定倒序解释。不能补写位编号；d是明确dont-care。 与既往卡诺图共享表示；决定性排除是原题索引映射歧义。|

|18|Prob025_reduction|排除|HISTORY_FUNCTIONAL_NEAR_DUPLICATE；in8,parity1，无时钟复位，XOR全部8位。 历史parity8为同一完整功能；另已读Prob052/122同类。|

|19|Prob138_2012_q2fsm|排除|WITHIN_ROUND_SUBSTANTIVE_OVERLAP；clk/reset/w/z1位，posedge同步高reset到A，E/F输出1，原12条转移完整；参考逐条一致，要求分离组合和时序always。 与更早135的六状态图在反相输入后完全同构；135虽因输出措辞排除，其完整状态图已在本轮暴露，保守排除重复结构。另含101检测子行为，与历史sequence101相关。|

|20|Prob130_circuit5|排除|KEY_FUNCTION_UNDERDETERMINED；a/b/c/d/e/q均4位，原表仅固定a=a,b=b,d=d,e=e并遍历c；可由常数查表或输入选择器同时解释，不能唯一推出参考mux函数。 历史mux同族亦暴露；首要排除为仅一组数据下波形不能确定全部输入映射。|

## 元数据阶段全部83项排除

|ID|原因|
|---|---|

|Prob001_zero|PRIOR_READ_OR_USED|

|Prob005_notgate|PRIOR_READ_OR_USED|

|Prob006_vectorr|PRIOR_READ_OR_USED|

|Prob009_popcount3|PRIOR_READ_OR_USED|

|Prob017_mux2to1v|PRIOR_READ_OR_USED|

|Prob018_mux256to1|PRIOR_READ_OR_USED|

|Prob019_m2014_q4f|PRIOR_READ_OR_USED|

|Prob021_mux256to1v|PRIOR_READ_OR_USED|

|Prob022_mux2to1|PRIOR_READ_OR_USED|

|Prob023_vector100r|PRIOR_READ_OR_USED|

|Prob024_hadd|CONSERVATIVE_HISTORY_FAMILY|

|Prob027_fadd|CONSERVATIVE_HISTORY_FAMILY|

|Prob029_m2014_q4g|PRIOR_READ_OR_USED|

|Prob030_popcount255|PRIOR_READ_OR_USED|

|Prob031_dff|PRIOR_READ_OR_USED|

|Prob032_vector0|PRIOR_READ_OR_USED|

|Prob033_ece241_2014_q1c|PRIOR_READ_OR_USED|

|Prob034_dff8|PRIOR_READ_OR_USED|

|Prob035_count1to10|PRIOR_READ_OR_USED|

|Prob037_review2015_count1k|PRIOR_READ_OR_USED|

|Prob038_count15|PRIOR_READ_OR_USED|

|Prob040_count10|PRIOR_READ_OR_USED|

|Prob041_dff8r|PRIOR_READ_OR_USED|

|Prob042_vector4|PRIOR_READ_OR_USED|

|Prob043_vector5|PRIOR_READ_OR_USED|

|Prob044_vectorgates|PRIOR_READ_OR_USED|

|Prob045_edgedetect2|CONSERVATIVE_HISTORY_FAMILY|

|Prob046_dff8p|PRIOR_READ_OR_USED|

|Prob047_dff8ar|CONSERVATIVE_HISTORY_FAMILY|

|Prob050_kmap1|PRIOR_READ_OR_USED|

|Prob052_gates100|PRIOR_READ_OR_USED|

|Prob054_edgedetect|CONSERVATIVE_HISTORY_FAMILY|

|Prob059_wire4|PRIOR_READ_OR_USED|

|Prob062_bugs_mux2|CONSERVATIVE_HISTORY_FAMILY|

|Prob063_review2015_shiftcount|CONSERVATIVE_HISTORY_FAMILY|

|Prob064_vector3|PRIOR_READ_OR_USED|

|Prob065_7420|PRIOR_READ_OR_USED|

|Prob066_edgecapture|CONSERVATIVE_HISTORY_FAMILY|

|Prob067_countslow|CONSERVATIVE_HISTORY_FAMILY|

|Prob068_countbcd|CONSERVATIVE_HISTORY_FAMILY|

|Prob071_always_casez|PRIOR_READ_OR_USED|

|Prob073_dff16e|CONSERVATIVE_HISTORY_FAMILY|

|Prob074_ece241_2014_q4|PRIOR_READ_OR_USED|

|Prob075_counter_2bc|CONSERVATIVE_HISTORY_FAMILY|

|Prob078_dualedge|CONSERVATIVE_HISTORY_FAMILY|

|Prob079_fsm3onehot|PRIOR_READ_OR_USED|

|Prob082_lfsr32|CONSERVATIVE_HISTORY_FAMILY|

|Prob084_ece241_2013_q12|PRIOR_READ_OR_USED|

|Prob085_shift4|CONSERVATIVE_HISTORY_FAMILY|

|Prob086_lfsr5|CONSERVATIVE_HISTORY_FAMILY|

|Prob087_gates|PRIOR_READ_OR_USED|

|Prob088_ece241_2014_q5b|PRIOR_READ_OR_USED|

|Prob089_ece241_2014_q5a|PRIOR_READ_OR_USED|

|Prob094_gatesv|PRIOR_READ_OR_USED|

|Prob095_review2015_fsmshift|PRIOR_READ_OR_USED|

|Prob096_review2015_fsmseq|PRIOR_READ_OR_USED|

|Prob097_mux9to1v|CONSERVATIVE_HISTORY_FAMILY|

|Prob100_fsm3comb|PRIOR_READ_OR_USED|

|Prob101_circuit4|PRIOR_READ_OR_USED|

|Prob104_mt2015_muxdff|CONSERVATIVE_HISTORY_FAMILY|

|Prob105_rotate100|PRIOR_READ_OR_USED|

|Prob106_always_nolatches|PRIOR_READ_OR_USED|

|Prob109_fsm1|PRIOR_READ_OR_USED|

|Prob111_fsm2s|PRIOR_READ_OR_USED|

|Prob114_bugs_case|PRIOR_READ_OR_USED|

|Prob115_shift18|CONSERVATIVE_HISTORY_FAMILY|

|Prob118_history_shift|CONSERVATIVE_HISTORY_FAMILY|

|Prob119_fsm3|PRIOR_READ_OR_USED|

|Prob120_fsm3s|CONSERVATIVE_HISTORY_FAMILY|

|Prob122_kmap4|PRIOR_READ_OR_USED|

|Prob123_bugs_addsubz|PRIOR_READ_OR_USED|

|Prob127_lemmings1|PRIOR_READ_OR_USED|

|Prob131_mt2015_q4|PRIOR_READ_OR_USED|

|Prob132_always_if2|PRIOR_READ_OR_USED|

|Prob141_count_clock|CONSERVATIVE_HISTORY_FAMILY|

|Prob143_fsm_onehot|PRIOR_READ_OR_USED|

|Prob145_circuit8|PRIOR_READ_OR_USED|

|Prob146_fsm_serialdata|PRIOR_READ_OR_USED|

|Prob149_ece241_2013_q4|PRIOR_READ_OR_USED|

|Prob150_review2015_fsmonehot|PRIOR_READ_OR_USED|

|Prob151_review2015_fsm|PRIOR_READ_OR_USED|

|Prob154_fsm_ps2data|PRIOR_READ_OR_USED|

|Prob155_lemmings4|PRIOR_READ_OR_USED|

完整20题接口/复位/有效域/参考/原TB刺激/依赖/作者/采样行号见B/selection.json；完整原题及ref/test（含18排除题）在B/originals，均保持原始字节。

## 统一完整system

```text
Implement the given digital circuit in synthesizable SystemVerilog.
Return only one complete module in a single ```systemverilog code block.
Use exactly the specified module name and ports. Do not provide a testbench.
No includes, preprocessor directives, strings, hierarchical references, extra
modules, simulation system tasks, file IO, or attributes. Only $signed,
$unsigned and $clog2 system functions are permitted. Do not use delays.
The independent evaluator will supply all input stimuli and check outputs.
```

## 冻结context模板

```text


<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified contiguous excerpts.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
{fragments}
</generic_reference_context>

```

## Prob055_conditional — 四数无符号最小值

a/b/c/d及min均8位；纯组合unsigned min(a,b,c,d)，相等时值相同，无优先输出索引、时钟或初始化要求。参考从a开始依次比较b/c/d。

历史rt_comparator是两数大小/相等标志；本题四操作数归约选择数值，非仅位宽替换；共享比较/选择原语明确保留为相关性。未发现同一完整min4行为。

原TB与限制：5组定向逐次改变最小值所在端口，100随机双边沿；不穷尽2^32输入空间。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_prompt.txt) SHA256 `a4cb1a6391988c0c0661808b8bafb625160c70dab00c917bc970be65aa9b34c7`；Git blob `1e002f2d4e003b77db9fa42e1ca8c8013b4465b4`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_ref.sv) SHA256 `2df6d288e7b4439de40d0225546cf1df4a17075bd577a73e6faf25f0ba6d0a2d`；Git blob `831e6502110f082ab23588d9d4f1dab9dd00825d`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_test.sv) SHA256 `01b9ae5a9b87c2349c37fb9bd616a63c9da460fd672e9ae8aedc8f2c378a7909`；Git blob `afe12939e1dc64f96be7cc064b916196050e2907`

### 完整原题 = no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a   (8 bits)
 - input  b   (8 bits)
 - input  c   (8 bits)
 - input  d   (8 bits)
 - output min (8 bits)

The module should find the minimum of the four input values. Unsigned
numbers can be compared with standard comparison operators (a < b).


```

### 自动检索结果

{
  "task": "Prob055_conditional",
  "selected_ids": [
    "GEN023",
    "GEN021",
    "GEN048"
  ],
  "scores": [
    0.2585716028233718,
    0.16394527947937185,
    0.1634311279079144
  ],
  "no_hit": false,
  "retrieval_seconds": 0.00894069999048952,
  "prompt_bytes": 409,
  "context_bytes": 5173
}

全部48段排名、逐词贡献、原始片段及行号见C/retrieval/Prob055_conditional.json。只检索一次，无人工换段或参数回调。

### 完整rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a   (8 bits)
 - input  b   (8 bits)
 - input  c   (8 bits)
 - input  d   (8 bits)
 - output min (8 bits)

The module should find the minimum of the four input values. Unsigned
numbers can be compared with standard comparison operators (a < b).



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified contiguous excerpts.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[GEN023; lowRISC Verilog Coding Style Guide; lines 1424-1511]
While cyclic dependencies are permitted by the SystemVerilog language
specification, their use can break some tools.

For example:

```systemverilog
package foo;

  // Package "bar" must not depend on anything in "foo":
  parameter int unsigned PageSizeBytes = 16 * bar::Kibi;

endpackage
```

### Module Declaration

***Use the Verilog-2001 full port declaration style, and use the format
below.***

Use the Verilog-2001 combined port and I/O declaration style. Do not use the
Verilog-95 list style. The port declaration in the module statement should fully
declare the port name, type, and direction.

The opening parenthesis should be on the same line as the module declaration,
and the first port should be declared on the following line.

The closing parenthesis should be on its own line, in column zero.

Indentation for module declaration follows the standard indentation
rule of two space indentation.

The clock port(s) must be declared first in the port list, followed by any and
all reset inputs.

Example without parameters:

&#x1f44d;
```systemverilog {.good}
module foo (
  input              clk_i,
  input              rst_ni,
  input [7:0]        d_i,
  output logic [7:0] q_o
);
```

Example with parameters:

&#x1f44d;
```systemverilog {.good}
module foo #(
  parameter int unsigned Width = 8,
) (
  input                    clk_i,
  input                    rst_ni,
  input [Width-1:0]        d_i,
  output logic [Width-1:0] q_o
);
```

Do not use Verilog-95 style:

&#x1f44e;
```systemverilog {.bad}
// WRONG:
module foo(a, b, c d);
input wire [2:0] a;
output logic b;
...
```

### Module Instantiation

***Use named ports to fully specify all instantiations.***

When connecting signals to ports for an instantiation, use the named port style,
like this:

```systemverilog
my_module i_my_instance (
  .clk_i (clk_i),
  .rst_ni(rst_ni),
  .d_i   (from_here),
  .q_o   (to_there)
);
```

If the port and the connecting signal have the same name, you can use the


[GEN021; lowRISC Verilog Coding Style Guide; lines 1295-1356]
Use common prefixes to identify groups of signals that operate together. For
example, all elements of an AXI-S interface would share a prefix: `foo_valid`,
`foo_ready`, and `foo_data`.

Additionally, prefixes should be used to clearly label which signal is in which
clock group for any module with multiple clocks. See the section on [clock
domains](#clocks) for more details.

Examples:

-   Signals associated with controlling a blockram might share a `bram_` prefix.
-   Signals that are synchronous with `clk_dram` rather than `clk` should share
    a `dram_` prefix.

Code example:

&#x1f44d;
```systemverilog {.good}
module fifo_controller (
  input         clk_i,
  input         rst_ni,

  // writer interface
  input [15:0]  wr_data_i,
  input         wr_valid_i,
  output        wr_ready_o,

  // reader interface
  output [15:0] rd_data_o,
  output        rd_valid_o,
  output [7:0]  rd_fullness_o,
  input         rd_ack_i,

  // memory interface:
  output [7:0]  mem_addr_o,
  output [15:0] mem_wdata_o,
  output        mem_we_o,
  input  [15:0] mem_rdata_i
);
```

This naming convention makes it easier to map port names onto similar signal
names using simple and consistent rules. See the section on [Hierarchical
Consistency](#hierarchical-consistency) for more information.

#### Hierarchical consistency

***The same signal should have the same name at any level of the hierarchy.***

A signal that connects to a port of an instance should have the same name as
that port. By proceeding in this manner, signals that are directly connected
should maintain the same name at any level of hierarchy.

Exceptions to this convention are expected, such as:

*   When connecting a port to an element of an array of signals.

*   When mapping a generic port name to something more specific to the design.
    For example, two generic blocks, one with a `host_bus` port and one with a
    `device_bus` port might be connected by a `foo_bar_bus` signal.

In each exceptional case, care should be taken to make the mapping of port names


[GEN048; lowRISC Verilog Coding Style Guide; lines 3162-3172]
* When printing use `0b` and `0x` as a prefix for binary and hex. Use
  `_` for clarity
* Use logical constructs (i.e `||`) for logical comparison, bit-wise
  (i.e `|`) for data comparison
* Bit vectors and packed arrays must be little-endian, unpacked arrays
  must be big-endian
* FSMs: **no logic** except for reset should be performed in the process
  for the state register
* A combinational process should first define **default value** of all
  outputs in the process
* Default value for next state variable should be the current state

</generic_reference_context>

```

## Prob124_rule110 — 512单元Rule110

clk/load1位，data/q512位；posedge，load优先同步装载；无复位，首次load前未定义。原8行局部真值完整，左右越界为0。参考零条件111、000、100与原表一致；511位右移切片在512位按位表达式上下文中零扩展，边界语义需未来工具验证，未编译。

历史移位器和相邻门题共享索引/邻居原语，但没有此512单元非线性局部规则迭代状态演化；不以共享基础语法本身排除。

原TB与限制：bit0/bit256种子、4df、一次$random扩展、清零及load变化；多个1000周期演化。随机32位值不能声称均匀512位。未独立穷尽邻域/边界/多步行为；无reset可测。

[prompt.txt](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_prompt.txt) SHA256 `3149f58c7fa9a5c9ac21216994a268ea5b143a9c0cd56872f8ea7835f10ecdd3`；Git blob `559ee5d2b9b16d978a6b6f76d5d984707d04c211`

[ref.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_ref.sv) SHA256 `c95a474c70bb071b1b8adc0c23a86822928a2c7cb20fde28b8e48cd6a19aad81`；Git blob `fb453ffac073c5ecc49c69c799b6cb04f2b68716`

[test.sv](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_test.sv) SHA256 `4099c733852aa603ff4ff244eb49d0712edd2df0834d68d6f827700a5ad57f00`；Git blob `25d993717a7ff4d8b5148580efb9d421251f2353`

### 完整原题 = no_rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  load
 - input  data (512 bits)
 - output q    (512 bits)

The module should implement Rule 110, a one-dimensional cellular
automaton with interesting properties (such as being Turing-complete).
There is a one-dimensional array of cells (on or off). At each time step,
the state of each cell changes. In Rule 110, the next state of each cell
depends only on itself and its two neighbours, according to the following
table:

  Left[i+1] | Center[i] | Right[i-1] | Center's next state 
  1         | 1         | 1          | 0
  1         | 1         | 0          | 1
  1         | 0         | 1          | 1
  1         | 0         | 0          | 0
  0         | 1         | 1          | 1
  0         | 1         | 0          | 1
  0         | 0         | 1          | 1
  0         | 0         | 0          | 0

In this circuit, create a 512-cell system (q[511:0]), and advance by one
time step each clock cycle. The synchronous active high load input
indicates the state of the system should be loaded with data[511:0].
Assume the boundaries (q[-1] and q[512], if they existed) are both zero
(off). Assume all sequential logic is triggered on the positive edge of the clock.


```

### 自动检索结果

{
  "task": "Prob124_rule110",
  "selected_ids": [
    "GEN022",
    "GEN023",
    "GEN021"
  ],
  "scores": [
    0.2926178761581124,
    0.20773384233762834,
    0.19979511301583125
  ],
  "no_hit": false,
  "retrieval_seconds": 0.009872100010397844,
  "prompt_bytes": 1355,
  "context_bytes": 6651
}

全部48段排名、逐词贡献、原始片段及行号见C/retrieval/Prob124_rule110.json。只检索一次，无人工换段或参数回调。

### 完整rag user

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  load
 - input  data (512 bits)
 - output q    (512 bits)

The module should implement Rule 110, a one-dimensional cellular
automaton with interesting properties (such as being Turing-complete).
There is a one-dimensional array of cells (on or off). At each time step,
the state of each cell changes. In Rule 110, the next state of each cell
depends only on itself and its two neighbours, according to the following
table:

  Left[i+1] | Center[i] | Right[i-1] | Center's next state 
  1         | 1         | 1          | 0
  1         | 1         | 0          | 1
  1         | 0         | 1          | 1
  1         | 0         | 0          | 0
  0         | 1         | 1          | 1
  0         | 1         | 0          | 1
  0         | 0         | 1          | 1
  0         | 0         | 0          | 0

In this circuit, create a 512-cell system (q[511:0]), and advance by one
time step each clock cycle. The synchronous active high load input
indicates the state of the system should be loaded with data[511:0].
Assume the boundaries (q[-1] and q[512], if they existed) are both zero
(off). Assume all sequential logic is triggered on the positive edge of the clock.



<generic_reference_context>
These are generic style excerpts, not new task requirements or solutions. The original specification above takes precedence.
Source: lowRISC contributors; CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); unmodified contiguous excerpts.
https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md
[GEN022; lowRISC Verilog Coding Style Guide; lines 1357-1423]
to signal names as unambiguous and consistent as possible.

### Clocks

***All clock signals must begin with `clk`.***

The main system clock for a design must be named `clk`. It is acceptable to use
`clk` to refer to the default clock that the majority of the logic in a module
is synchronous with.

If a module contains multiple clocks, the clocks that are not the system clock
should be named with a unique identifier, preceded by the `clk_` prefix. For
example: `clk_dram`, `clk_axi`, etc. Note that this prefix will be
used to identify other signals in that clock domain.

### Resets

***Resets are active-low and asynchronous. The default name is `rst_n`.***

Chip wide all resets are defined as active low and asynchronous. Thus they are
defined as tied to the asynchronous reset input of the associated standard
cell registers.

The default name is `rst_n`. If they must be distinguished by their clock, the
clock name should be included in the reset name like `rst_domain_n`.

SystemVerilog allows either of the following syntax styles, but the style
guide prefers the former.

```systemverilog
// preferred
always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    q <= 1'b0;
  end else begin
    q <= d;
  end
end

// legal but not preferred
always_ff @(posedge clk, negedge rst_n) begin
  if (!rst_n) begin
    q <= 1'b0;
  end else begin
    q <= d;
  end
end
```

## Language Features

### Preferred SystemVerilog Constructs

Use these SystemVerilog constructs instead of their Verilog-2001 equivalents:

-   `always_comb` is required over `always @*`.
-   `logic` is preferred over `reg` and `wire`.
-   Top-level `parameter` declarations are preferred over `` `define`` globals.


### Package Dependencies

***Packages must not have cyclic dependencies.***

Package files may depend on constants and types in other package files, but
there must not be any cyclic dependencies. That is: if package A depends on a
constant from package B, package B must not depend on anything from package A.


[GEN023; lowRISC Verilog Coding Style Guide; lines 1424-1511]
While cyclic dependencies are permitted by the SystemVerilog language
specification, their use can break some tools.

For example:

```systemverilog
package foo;

  // Package "bar" must not depend on anything in "foo":
  parameter int unsigned PageSizeBytes = 16 * bar::Kibi;

endpackage
```

### Module Declaration

***Use the Verilog-2001 full port declaration style, and use the format
below.***

Use the Verilog-2001 combined port and I/O declaration style. Do not use the
Verilog-95 list style. The port declaration in the module statement should fully
declare the port name, type, and direction.

The opening parenthesis should be on the same line as the module declaration,
and the first port should be declared on the following line.

The closing parenthesis should be on its own line, in column zero.

Indentation for module declaration follows the standard indentation
rule of two space indentation.

The clock port(s) must be declared first in the port list, followed by any and
all reset inputs.

Example without parameters:

&#x1f44d;
```systemverilog {.good}
module foo (
  input              clk_i,
  input              rst_ni,
  input [7:0]        d_i,
  output logic [7:0] q_o
);
```

Example with parameters:

&#x1f44d;
```systemverilog {.good}
module foo #(
  parameter int unsigned Width = 8,
) (
  input                    clk_i,
  input                    rst_ni,
  input [Width-1:0]        d_i,
  output logic [Width-1:0] q_o
);
```

Do not use Verilog-95 style:

&#x1f44e;
```systemverilog {.bad}
// WRONG:
module foo(a, b, c d);
input wire [2:0] a;
output logic b;
...
```

### Module Instantiation

***Use named ports to fully specify all instantiations.***

When connecting signals to ports for an instantiation, use the named port style,
like this:

```systemverilog
my_module i_my_instance (
  .clk_i (clk_i),
  .rst_ni(rst_ni),
  .d_i   (from_here),
  .q_o   (to_there)
);
```

If the port and the connecting signal have the same name, you can use the


[GEN021; lowRISC Verilog Coding Style Guide; lines 1295-1356]
Use common prefixes to identify groups of signals that operate together. For
example, all elements of an AXI-S interface would share a prefix: `foo_valid`,
`foo_ready`, and `foo_data`.

Additionally, prefixes should be used to clearly label which signal is in which
clock group for any module with multiple clocks. See the section on [clock
domains](#clocks) for more details.

Examples:

-   Signals associated with controlling a blockram might share a `bram_` prefix.
-   Signals that are synchronous with `clk_dram` rather than `clk` should share
    a `dram_` prefix.

Code example:

&#x1f44d;
```systemverilog {.good}
module fifo_controller (
  input         clk_i,
  input         rst_ni,

  // writer interface
  input [15:0]  wr_data_i,
  input         wr_valid_i,
  output        wr_ready_o,

  // reader interface
  output [15:0] rd_data_o,
  output        rd_valid_o,
  output [7:0]  rd_fullness_o,
  input         rd_ack_i,

  // memory interface:
  output [7:0]  mem_addr_o,
  output [15:0] mem_wdata_o,
  output        mem_we_o,
  input  [15:0] mem_rdata_i
);
```

This naming convention makes it easier to map port names onto similar signal
names using simple and consistent rules. See the section on [Hierarchical
Consistency](#hierarchical-consistency) for more information.

#### Hierarchical consistency

***The same signal should have the same name at any level of the hierarchy.***

A signal that connects to a port of an instance should have the same name as
that port. By proceeding in this manner, signals that are directly connected
should maintain the same name at any level of hierarchy.

Exceptions to this convention are expected, such as:

*   When connecting a port to an element of an array of signals.

*   When mapping a generic port name to something more specific to the design.
    For example, two generic blocks, one with a `host_bus` port and one with a
    `device_bus` port might be connected by a `foo_bar_bus` signal.

In each exceptional case, care should be taken to make the mapping of port names

</generic_reference_context>

```

## 预算与审核边界

2×3准确模型×2条件×2样本=24最大待审机会；上限96不是必须补足。gpt-5.6-luna/terra/sol各条件完整messages逐字相同，样本重复请求仅槽ID不同；发送字段只model因模型改变，不附参考RTL/TB。temperature/seed/reasoning省略。并发1，180秒/请求，HTTP1MiB、文本128KiB、job8MiB、run512MiB；无8192cap、无整批墙时cap。

预约消耗机会，未知/服务/传输/协议/哈希/资源异常立即停，不自动重试、补样、续写、fallback或扩批；实际usage原始保留，缺失null，费用不编造。固定OpenRouter路线仅离线配置，没有探针、账户访问或新HTTP模型请求。此包未证明服务端无内部包装。旧生产放行/账本及硬编码旧题的执行器均不可直接复用。

先总控及用户审阅本包；工具兼容/参考校准/独立判据和新执行器映射需要另案冻结审核，本次没有运行。仅两题且共享一般组合/索引原语，不能支持总体RAG收益或独立功能族数量结论。下一步尚未授权。

## 阶段封存时间

{
  "A": {
    "frozen_utc": "2026-10-24T07:00:39.712682+00:00",
    "a_lock_sha256": "26c135ff0b3153f3bda3e2ae57ccbb1c594118327593bb6d46a558e655fb8b9c",
    "protocol_lock_sha256": "a4514adde3c10f60290f2e73add971d483dda53f2dcf7626071bfb14a8dc9cbf",
    "source_count": 1,
    "chunks": 48,
    "new_candidate_content_reads": 0,
    "cognitive_blind": false
  },
  "B": {
    "frozen_utc": "2026-10-24T07:08:31.510161+00:00",
    "b_lock_sha256": "7259e338982e338356089c40785c45a3fd1f842527df15bcb64da2779dc5c01c",
    "a_lock_sha256": "26c135ff0b3153f3bda3e2ae57ccbb1c594118327593bb6d46a558e655fb8b9c",
    "protocol_lock_sha256": "a4514adde3c10f60290f2e73add971d483dda53f2dcf7626071bfb14a8dc9cbf",
    "selected_ids": [
      "Prob055_conditional",
      "Prob124_rule110"
    ],
    "retrieval_calls_so_far": 0
  },
  "C_start": {
    "utc": "2026-10-24T07:10:01.242200+00:00",
    "a_lock_sha256": "26c135ff0b3153f3bda3e2ae57ccbb1c594118327593bb6d46a558e655fb8b9c",
    "b_lock_sha256": "7259e338982e338356089c40785c45a3fd1f842527df15bcb64da2779dc5c01c",
    "plan_lock_sha256": "7bb1173cb433d88960f3cc2be0c7e5db6767524be6ada18b30db480a3adbe7ed",
    "retrieval_count_before": 0
  }
}
