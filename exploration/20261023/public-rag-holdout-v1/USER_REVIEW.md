# 待审公开原题与实际检索

状态：PREPARED_BLOCKED。仅离线准备，模型/embedding/rerank/compile/sim/SAT 均0。先总控审核，再由用户确认；本文件不是执行许可。

资料库与方法在新候选正文读取前冻结。A冻结时间 2026-10-23T01:10:43.076841+00:00；B读取开始 2026-10-23T01:10:54.740347+00:00；B选择封存 2026-10-23T02:28:50.511850+00:00。A锁 c0609d940a0e586e2b7b5fc81ca6d58bd1eeee5e1d4cecbe40415317f341ead1。

156个元数据ID→43个历史/家族排除→113个固定哈希排序→只读取首20个→12个静态合格、8个排除→按固定顺序取首5个；余7个合格但受上限未选，另93个未读。全部理由见 B/selection.json。未使用检索效果选题。

任务来源 NVlabs/verilog-eval，commit c498220d0a52248f8e3fdffe279075215bde2da6；MIT许可原文见 A/metadata/dataset-LICENSE。模型训练是否见过这些公开题 UNKNOWN；这里只主张未参与本地本方法调整，不主张训练污染已排除。

所有原题/参考/测试已逐字绑定git blob，原题文件和下方英文段保持字节；中文解释、资格判断、检索片段和system均是分开的项目材料。原参考与测试同源，不是独立oracle。原题仅发送prompt，绝不发送参考/test/中文解释。

## 项目统一system（不是上游题目）

```text
Implement the given digital circuit in synthesizable SystemVerilog.
Return only one complete module in a single ```systemverilog code block.
Use exactly the specified module name and ports. Do not provide a testbench.
No includes, preprocessor directives, strings, hierarchical references, extra
modules, simulation system tasks, file IO, or attributes. Only $signed,
$unsigned and $clog2 system functions are permitted. Do not use delays.
The independent evaluator will supply all input stimuli and check outputs.```


## Prob089_ece241_2014_q5a（固定候选序号2）

中文释义：串行二进制补码。

入选依据与限制：任意长度LSB先入的串行补码Moore机，posedge与高有效异步reset明确。不同于并行adder8/ve_addsub、奇偶累计或固定序列检测；串行携带“首次1已见”状态是不同完整契约。复位期间输出由参考固定为0，原文停止转换、复位初态的自然解释仍需用户确认，不增补prompt。

[公开原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob089_ece241_2014_q5a_prompt.txt) · [原参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob089_ece241_2014_q5a_ref.sv) · [原测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob089_ece241_2014_q5a_test.sv)

原题 SHA256：a11b8fb0439936a0b5020c5ad496e080ccc0ddae57a3614c3c857ed337c50743

### 完整上游原文

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  areset
 - input  x
 - output z

The module should implement a one-input one-output serial 2's
complementer Moore state machine. The input (x) is a series of bits (one
per clock cycle) beginning with the least-significant bit of the number,
and the output (Z) is the 2's complement of the input. The machine will
accept input numbers of arbitrary length. The circuit requires a positive
edge triggered asynchronous reset. The conversion begins when Reset is
released and stops when Reset is asserted. Assume all sequential logic is
triggered on the positive edge of the clock.

```

### 覆盖与独立性

异步reset_test(1)、定向位序列、400个双边沿随机reset/x事件；不是任意长度穷尽。 同源参考未运行；新额外验证未适配。

### 实际检索（自动取固定top3，无人工替换）


LR018 / Case Statements / score=8.635117229532888 / [原文L2245-L2252](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2245-L2252) / SHA256 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

```text
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.
```


LR006 / Sequential Logic (Registers) / score=8.06316118648462 / [原文L1818-L1820](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L1818-L1820) / SHA256 e21796acf251a073061ee4e103ad61404d82cbafca689dc2df125e2c0df8e647

```text
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.
```


LR015 / Case Statements / score=8.028244543821076 / [原文L2189-L2192](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2189-L2192) / SHA256 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


完整18片段排名与逐词贡献：C/retrieval/Prob089_ece241_2014_q5a.json。完整待发messages：C/messages/Prob089_ece241_2014_q5a__no_rag.json 与 Prob089_ece241_2014_q5a__rag.json；三模型两样本引用相同内容，实际服务包装仍待核。


## Prob023_vector100r（固定候选序号5）

中文释义：100位向量反序。

入选依据与限制：索引i接99-i的固定排列；不同于历史可变移位/循环旋转，非同函数宽度变体。接口与排列定义完整。

[公开原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob023_vector100r_prompt.txt) · [原参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob023_vector100r_ref.sv) · [原测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob023_vector100r_test.sv)

原题 SHA256：bc7e2b7e746c0e5b65c6f15b193407f378c575b59ffbda537c43a19b2e3e540b

### 完整上游原文

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in  (100 bits)
 - output out (100 bits)

The module should reverse the bit ordering of the input and write to the
output.

```

### 覆盖与独立性

两边沿更新100位随机输入，100个negedge后结束；非2^100穷尽。 同源参考未运行；新额外验证未适配。

### 实际检索（自动取固定top3，无人工替换）


LR018 / Case Statements / score=3.7475288712241452 / [原文L2245-L2252](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2245-L2252) / SHA256 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

```text
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.
```


LR015 / Case Statements / score=3.404362645465794 / [原文L2189-L2192](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2189-L2192) / SHA256 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003 / Sequential Logic (Latches) / score=2.969023870581372 / [原文L1802-L1803](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L1802-L1803) / SHA256 bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


完整18片段排名与逐词贡献：C/retrieval/Prob023_vector100r.json。完整待发messages：C/messages/Prob023_vector100r__no_rag.json 与 Prob023_vector100r__rag.json；三模型两样本引用相同内容，实际服务包装仍待核。


## Prob146_fsm_serialdata（固定候选序号6）

中文释义：串行字节接收。

入选依据与限制：0起始+8位LSB载荷+1停止、错误停止恢复、仅done时载荷有效、同步高有效reset完整。与framed_parity的固定4位奇偶帧、escape_frame的2位转义token/XOR计数、I2C时钟总线控制均非同一完整契约；共享移位/帧状态原语披露。末句done遇stop按前文“correctly received”解释，错误帧恢复stop不交付；该语境解释须总控核对，不能把参考实现加进prompt。

[公开原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob146_fsm_serialdata_prompt.txt) · [原参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob146_fsm_serialdata_ref.sv) · [原测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob146_fsm_serialdata_test.sv)

原题 SHA256：937a83f95389e73c9561b40f1305963b474e058b18f41949b3a7a54aae7b8395

### 完整上游原文

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  in
 - input  reset
 - output out_byte (8 bits)
 - output done

In many (older) serial communications protocols, each data byte is sent
along with a start bit and a stop bit, to help the receiver delimit bytes
from the stream of bits. One common scheme is to use one start bit (0), 8
data bits, and 1 stop bit (1). The line is also at logic 1 when nothing
is being transmitted (idle). Design a finite state machine that will
identify when bytes have been correctly received when given a stream of
bits. It needs to identify the start bit, wait for all 8 data bits, then
verify that the stop bit was correct. The module will also output the
correctly-received data byte. `out_byte` needs to be valid when `done` is
1, and is don't-care otherwise. If the stop bit does not appear when
expected, the FSM must wait until it finds a stop bit before attempting
to receive the next byte. Include a active-high synchronous reset. Note
that the serial protocol sends the least significant bit first. It should
assert done each time it finds a stop bit. Assume all sequential logic is
triggered on the positive edge of the clock.

```

### 覆盖与独立性

启动reset、9/10拍低电平的有效/缺失停止序列、800个双边沿随机in/reset事件；out_byte参考为X时不评分。非全载荷/复位相位穷尽。 同源参考未运行；新额外验证未适配。

### 实际检索（自动取固定top3，无人工替换）


LR006 / Sequential Logic (Registers) / score=11.650807732005813 / [原文L1818-L1820](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L1818-L1820) / SHA256 e21796acf251a073061ee4e103ad61404d82cbafca689dc2df125e2c0df8e647

```text
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.
```


LR015 / Case Statements / score=7.857028088115966 / [原文L2189-L2192](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2189-L2192) / SHA256 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR018 / Case Statements / score=7.4950577424482905 / [原文L2245-L2252](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2245-L2252) / SHA256 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

```text
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.
```


完整18片段排名与逐词贡献：C/retrieval/Prob146_fsm_serialdata.json。完整待发messages：C/messages/Prob146_fsm_serialdata__no_rag.json 与 Prob146_fsm_serialdata__rag.json；三模型两样本引用相同内容，实际服务包装仍待核。


## Prob032_vector0（固定候选序号9）

中文释义：三位向量拆线。

入选依据与限制：明确outv原样输出、o0/o1/o2按位输出；与decoder3的onehot解码、mux8的选择函数不同。没有状态/复位语义缺口。

[公开原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob032_vector0_prompt.txt) · [原参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob032_vector0_ref.sv) · [原测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob032_vector0_test.sv)

原题 SHA256：86607e1d27d54efeeb53ee5574c6884b1b51ab855b693422cf6c1bfdaba98ca0

### 完整上游原文

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  vec  (3 bits)
 - output outv (3 bits)
 - output o2
 - output o1
 - output o0

The module has one 3-bit input, then outputs the same vector, and also
splits it into three separate 1-bit outputs. Connect output o0 to the
input vector's position 0, o1 to position 1, etc.

```

### 覆盖与独立性

count++驱动10次3位vec，静态可见覆盖0..7并回绕；实际采样数/通过与工具语义未经运行核验。 同源参考未运行；新额外验证未适配。

### 实际检索（自动取固定top3，无人工替换）


LR018 / Case Statements / score=3.7475288712241452 / [原文L2245-L2252](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2245-L2252) / SHA256 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

```text
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.
```


LR015 / Case Statements / score=3.404362645465794 / [原文L2189-L2192](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2189-L2192) / SHA256 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR008 / Sequential Logic (Registers) / score=3.394616774574386 / [原文L1897-L1901](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L1897-L1901) / SHA256 21c198d95c6a31cf2ed9e901a11384008476b278830e4a0be73c3c5feb192946

```text
Keep work in sequential blocks simple. If a sequential block becomes
sufficiently complicated, consider splitting the combinational logic into a
separate combinational (`always_comb`) block. Ideally, sequential blocks should
contain only a register instantiation, with perhaps a load enable or an
increment.
```


完整18片段排名与逐词贡献：C/retrieval/Prob032_vector0.json。完整待发messages：C/messages/Prob032_vector0__no_rag.json 与 Prob032_vector0__rag.json；三模型两样本引用相同内容，实际服务包装仍待核。


## Prob064_vector3（固定候选序号10）

中文释义：向量拼接拆分。

入选依据与限制：六个5位输入按列举a..f顺序拼接，末尾二个1，按w/x/y/z顺序拆成32位。参考与列举顺序一致；原文没有显式拼接等式，顺序解释在审阅说明中披露，不写回原题。与历史shift/mux功能不同。

[公开原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob064_vector3_prompt.txt) · [原参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob064_vector3_ref.sv) · [原测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob064_vector3_test.sv)

原题 SHA256：ff98e7fba9109a1736b495bc5a2b9fe1c5e8f058e97fe511ecf1cb330c5b1da9

### 完整上游原文

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a (5 bits)
 - input  b (5 bits)
 - input  c (5 bits)
 - input  d (5 bits)
 - input  e (5 bits)
 - input  f (5 bits)
 - output w (8 bits)
 - output x (8 bits)
 - output y (8 bits)
 - output z (8 bits)

The module should concatenate the input vectors together then split them
up into several output vectors. There are six 5-bit input vectors: a, b,
c, d, e, and f, for a total of 30 bits of input. There are four 8-bit
output vectors: w, x, y, and z, for 32 bits of output. The output should
be a concatenation of the input vectors followed by two 1 bits (the two 1
bits should be in the LSB positions).

```

### 覆盖与独立性

零、1到0x400单比特、交替5位分组和100个双边沿随机输入；不是30位输入穷尽，也未覆盖全部walking-one位置。 同源参考未运行；新额外验证未适配。

### 实际检索（自动取固定top3，无人工替换）


LR018 / Case Statements / score=8.635117229532888 / [原文L2245-L2252](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2245-L2252) / SHA256 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

```text
`casex` should not be used. `casex` implements a symmetric wildcard operator
such that an `X` in the case expression may match one or more case items.
`casez` only treats high-impedance states (`Z` or `?`) as a wildcard, and
performs exact matches for undriven `X` inputs. While this does not completely
fix the problems with symmetric wildcard matching, it is harder to accidentally
produce a `Z` input than an `X` input, so this form is preferred.
`case inside` does not treat either `X` or `Z` in the case expression as a
wildcard, so this form is preferred over `casez`.
```


LR015 / Case Statements / score=5.036393734203968 / [原文L2189-L2192](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L2189-L2192) / SHA256 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003 / Sequential Logic (Latches) / score=2.969023870581372 / [原文L1802-L1803](https://github.com/lowRISC/style-guides/blob/9c15ff5dce23eef969e00ab3715153967419eadd/VerilogCodingStyle.md#L1802-L1803) / SHA256 bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


完整18片段排名与逐词贡献：C/retrieval/Prob064_vector3.json。完整待发messages：C/messages/Prob064_vector3__no_rag.json 与 Prob064_vector3__rag.json；三模型两样本引用相同内容，实际服务包装仍待核。


## 方法冻结与局限

A采用原18片段lowRISC库和原检索器，没有根据新题改资料/分段/停用词/同义词/词形/top-k/排序/包装/预算。纯词法BM25，无词形或同义词处理；完整排名保留。片段是一般风格建议，不是答案，也不是规范语言标准；检索相似度不证明适用性或收益。不得用观察结果重新择题或换片段。


## 预算与执行门槛

五题×三模型×两条件×两样本=60槽，全部NOT_STARTED，替代旧准备、不叠加旧24/60/30槽。每次8192 completion token，最大491520；并发1，单请求180秒，模型阶段12000秒，全批28800秒。返回文本128KiB/HTTP1MiB；不重试、不补样，未知预约占机会且停新调用，403/不支持模型/传输或包装异常立即停。真实token与费用当前0模型调用，未来单价/实际费用UNKNOWN，不能把token上限当固定费用。

服务隐藏包装是否一致、completion硬上限是否实际执行、三指定模型与共同参数支持、正式执行器、原参考校准和新题额外验证适配均仍阻断。温度/seed/reasoning统一省略不代表默认行为已证相同。只有本地拟请求一致，未证明实际请求一致。

后续参考校准只是另待批准的最多5compile+5sim建议（15s/10s，首次基础设施异常停），本轮不执行；不能重复此前COMSPEC定位或默认代理失败回归。SAT14/32与事件/复位能力需逐题契约审查，不能把未支持题当PASS。


## 如实保留的负观察与核验范围

五题均有正分片段，但向量反序和拼接也取回case通配/默认分支及latch建议，与其纯连线需求贴合弱；不能把有命中当有效帮助。五题独立离线检索合计约3.67ms（不含进程启动/加载），不是模型延迟或总体时间收益。结果保持原样，未调方法。

本地核验确认A30文件、B67文件、C93文件的精确集合及hash、完整原题字节和60拟请求同条件一致。另复核旧公开155文件、旧RAG118文件、97基线绑定与22复用源绑定；旧默认24 tests/3 failures/1 error/2 skipped/exit1仍保留，没有证明代理根因，也未重跑。旧v2完整条件15/16、校准exit1不改。当前服务配置只有禁用占位ID和启用DEMO_NOT_REAL，不支持声称三目标模型可执行。

B的资格判断是静态人工审阅，仍请总控独立核对Prob089复位输出、Prob146末句stop与错误恢复的上下文解释、Prob064列举顺序解释及历史近重复判断。若发现资格问题，保留当前封存负结果，不回填候选或修改A/原文；由总控和用户决定后续。
