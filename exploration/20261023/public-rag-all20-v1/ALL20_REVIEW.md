# 固定20题执行补充包（模型生成尚未启动）

范围来自用户最新授权：旧B全部20题，不再筛选或补题。240是总尝试上限，替代旧60/24/30方案。全部题测试不等于全部合格holdout。原参考一致性与合规清晰两题子集分别报告。

A文件、检索器、参数、包装原字节复用。仅外层数量预算明确从5题60槽改为20题240槽，A/budget-policy.json保留为历史原件，当前数量以本包execution-policy.json为准。


## 1. Prob149_ece241_2013_q4 — 水位控制

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / SPEC_REFERENCE_CONFLICT。

原依据：原文要求水位上升时打开 dfr；参考 A2→B1(水位000→001)给0110，即dfr=0，而下降C1→B2给0111。方向相反，不能改原文或参考。测试包含上升下降序列。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob149_ece241_2013_q4_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob149_ece241_2013_q4_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob149_ece241_2013_q4_test.sv)；MIT，固定commit。

原题SHA256：93563fc3ecec7a35eec28f4a4ed1e09393cf21ab8ae3c57cd0de1219bf1f0e8d

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  s (3 bits)
 - output fr2
 - output fr1
 - output fr0
 - output dfr

A large reservior of water serves several users. In order to keep the
level of water succificently high, three sensors are placed vertically at
5-inch intervals. When the water level is above the highest sensor s[2],
the input flow rate should be zero. When the level is below the lowest
sensor s[0], the flow rate should be at maximum (both Nominal flow valve
and Supplemental flow valve opened). The flow rate when the level is
between the upper and lower sensors is determined by two factors: the
water level and the level previous to the last sensor change. Each water
level has a nominal flow rate associated with it as show in the table
below. If the sensor change indicates that the previous level was lower
than the current level, the flow rate should be increased by opening the
Supplemental flow valve (controlled by dfr).

  Water Level           | Sensors Asserted | Nominal Flow Rate Inputs to be Asserted
  Above s[2]            | s[0], s[1], s[2] | None
  Between s[2] and s[1] | s[0], s[1]       | fr0
  Between s[1] and s[0] | s[0]             | fr0, fr1
  Below s[0]            | None             | fr0, fr1, fr2

Also include an active-high synchronous reset that resets the state
machine to a state equivalent to if the water level had been low for a
long time (no sensors asserted, and all four outputs asserted).

```

自动检索：LR015, LR018, LR010；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob149_ece241_2013_q4.json，完整实际拟消息见messages/Prob149_ece241_2013_q4__rag.json和__no_rag.json。


LR015，score=10.583383326679087，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR018，score=7.799845547312677，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR010，score=6.391947200025895，Combinational Logic，L2152-2153，SHA f1044589bb7940ec2cb3d3cd0e6488dcce2a40da913569935f328601dce6cf4f

```text
Do not use three-state logic (`Z` state) to accomplish on-chip logic such as
muxing.
```


## 2. Prob089_ece241_2014_q5a — 串行二进制补码

标签：AMBIGUOUS_RESET_OUTPUT；原标签：SELECTED_CONDITIONAL / ELIGIBLE。

原依据：任意长度LSB先入的串行补码Moore机，posedge与高有效异步reset明确。不同于并行adder8/ve_addsub、奇偶累计或固定序列检测；串行携带“首次1已见”状态是不同完整契约。复位期间输出由参考固定为0，原文停止转换、复位初态的自然解释仍需用户确认，不增补prompt。

总控后续语义裁决覆盖原条件性解释，见coordinator-semantic-review.md。

[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob089_ece241_2014_q5a_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob089_ece241_2014_q5a_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob089_ece241_2014_q5a_test.sv)；MIT，固定commit。

原题SHA256：a11b8fb0439936a0b5020c5ad496e080ccc0ddae57a3614c3c857ed337c50743

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

自动检索：LR018, LR006, LR015；EXACT_REUSE_PRIOR_FROZEN_RESULT；完整18排名/逐词分数/全文见retrieval/Prob089_ece241_2014_q5a.json，完整实际拟消息见messages/Prob089_ece241_2014_q5a__rag.json和__no_rag.json。


LR018，score=8.635117229532888，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR006，score=8.06316118648462，Sequential Logic (Registers)，L1818-1820，SHA e21796acf251a073061ee4e103ad61404d82cbafca689dc2df125e2c0df8e647

```text
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.
```


LR015，score=8.028244543821076，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


## 3. Prob029_m2014_q4g — 三输入XNOR/XOR

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / HISTORY_NEAR_DUPLICATE。

原依据：等价于3位奇偶归约取反；相对历史parity8只是宽度和输出极性变化，保守排除。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob029_m2014_q4g_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob029_m2014_q4g_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob029_m2014_q4g_test.sv)；MIT，固定commit。

原题SHA256：a2b500b28376a1ca341e9e49bf5a44640e4258cef6a34c4e3ab59e5e1febf9fc

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in1
 - input  in2
 - input  in3
 - output out

The module should impement the following circuit: A two-input XNOR
(connected to 'in1' and 'in2) has an output connected to the input of a
two-input XOR. The second input of the XOR is 'in3.' The output of the
XOR is 'out'.

```

自动检索：LR018, LR015, LR003；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob029_m2014_q4g.json，完整实际拟消息见messages/Prob029_m2014_q4g__rag.json和__no_rag.json。


LR018，score=3.7475288712241452，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=2.969023870581372，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 4. Prob131_mt2015_q4 — 组合子模块

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / WRAPPER_STRUCTURE_CONFLICT。

原依据：原文明确两A两B子模块实例，且未指定顶层模块名；冻结system只允许一个指定名模块。不能添TopModule要求或静默取消结构要求。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob131_mt2015_q4_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob131_mt2015_q4_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob131_mt2015_q4_test.sv)；MIT，固定commit。

原题SHA256：6688d1b4a6ab649dfeb5f62bde7ed3e69567f45d2e866c07801589d8aa7516a6

```text

Module A implements the boolean function z = (x^y) & x.

Module B can be described by the following simulation waveform:

  time  x  y  z
  0ns   0  0  1
  5ns   0  0  1
  10ns  0  0  1
  15ns  0  0  1
  20ns  0  0  1
  25ns  1  0  0
  30ns  1  0  0
  35ns  0  1  0
  40ns  0  1  0
  45ns  1  1  1
  50ns  1  1  1
  55ns  0  0  1
  60ns  0  1  0
  65ns  0  1  0
  70ns  1  1  1
  75ns  0  1  0
  80ns  0  1  0
  85ns  0  1  0
  90ns  1  0  0

Now consider a top-level module with the following interface:

 - input  x
 - input  y
 - output z

The module is implemented with two A submodules and two B submodules. The
first input of all four submodules is connect to input 'x', and the
second input of all four submodules is connected to 'y'. The output of
the first A submodule is connected to a two-input OR, along with the
output of the first B submodule. The second pair of A and B submodules is
similarly connected to an AND gate. The output of the OR and the AND is
connected to an XOR, whose output is 'z'.

```

自动检索：LR018, LR011, LR015；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob131_mt2015_q4.json，完整实际拟消息见messages/Prob131_mt2015_q4__rag.json和__no_rag.json。


LR018，score=8.635117229532888，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR011，score=4.60260140685691，Combinational Logic，L2155-2156，SHA 11ca5a6104937992e53302ca7cbcbd7ec17dc439af10fb1c09ed6fed54644ef7

```text
Do not infer a latch inside a function, as this may cause a
simulation/synthesis mismatch.
```


LR015，score=3.856446614443349，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


## 5. Prob023_vector100r — 100位向量反序

标签：CONFIRMED_CLEAR_SUBSET；原标签：SELECTED_CONDITIONAL / ELIGIBLE。

原依据：索引i接99-i的固定排列；不同于历史可变移位/循环旋转，非同函数宽度变体。接口与排列定义完整。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob023_vector100r_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob023_vector100r_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob023_vector100r_test.sv)；MIT，固定commit。

原题SHA256：bc7e2b7e746c0e5b65c6f15b193407f378c575b59ffbda537c43a19b2e3e540b

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in  (100 bits)
 - output out (100 bits)

The module should reverse the bit ordering of the input and write to the
output.

```

自动检索：LR018, LR015, LR003；EXACT_REUSE_PRIOR_FROZEN_RESULT；完整18排名/逐词分数/全文见retrieval/Prob023_vector100r.json，完整实际拟消息见messages/Prob023_vector100r__rag.json和__no_rag.json。


LR018，score=3.7475288712241452，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=2.969023870581372，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 6. Prob146_fsm_serialdata — 串行字节接收

标签：AMBIGUOUS_ERROR_RECOVERY_DONE；原标签：SELECTED_CONDITIONAL / ELIGIBLE。

原依据：0起始+8位LSB载荷+1停止、错误停止恢复、仅done时载荷有效、同步高有效reset完整。与framed_parity的固定4位奇偶帧、escape_frame的2位转义token/XOR计数、I2C时钟总线控制均非同一完整契约；共享移位/帧状态原语披露。末句done遇stop按前文“correctly received”解释，错误帧恢复stop不交付；该语境解释须总控核对，不能把参考实现加进prompt。

总控后续语义裁决覆盖原条件性解释，见coordinator-semantic-review.md。

[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob146_fsm_serialdata_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob146_fsm_serialdata_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob146_fsm_serialdata_test.sv)；MIT，固定commit。

原题SHA256：937a83f95389e73c9561b40f1305963b474e058b18f41949b3a7a54aae7b8395

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

自动检索：LR006, LR015, LR018；EXACT_REUSE_PRIOR_FROZEN_RESULT；完整18排名/逐词分数/全文见retrieval/Prob146_fsm_serialdata.json，完整实际拟消息见messages/Prob146_fsm_serialdata__rag.json和__no_rag.json。


LR006，score=11.650807732005813，Sequential Logic (Registers)，L1818-1820，SHA e21796acf251a073061ee4e103ad61404d82cbafca689dc2df125e2c0df8e647

```text
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.
```


LR015，score=7.857028088115966，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR018，score=7.4950577424482905，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


## 7. Prob033_ece241_2014_q1c — 有符号加法溢出

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / HISTORY_NEAR_DUPLICATE。

原依据：核心8位加法与历史adder8/alu8/saturating8/ve_addsub重合，仅符号溢出标志差异；保守排除。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob033_ece241_2014_q1c_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob033_ece241_2014_q1c_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob033_ece241_2014_q1c_test.sv)；MIT，固定commit。

原题SHA256：e0af17e9255b0a9cc227c1fc506c6def2c13a044e9422a1eae329c766772f68b

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a (8 bits)
 - input  b (8 bits)
 - output s (8 bits)
 - output overflow

Assume that you have two 8-bit 2's complement numbers, a[7:0] and b[7:0].
The module should add these numbers to produce s[7:0]. Also compute
whether a (signed) overflow has occurred.

```

自动检索：LR018, LR015, LR003；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob033_ece241_2014_q1c.json，完整实际拟消息见messages/Prob033_ece241_2014_q1c__rag.json和__no_rag.json。


LR018，score=5.1954021019231345，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=2.969023870581372，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 8. Prob132_always_if2 — 补全条件分支

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / SPEC_AMBIGUITY。

原依据：原题标题adder-subtractor与cpu/驾驶端口冲突；只说fix bug，未给未命中条件输出契约，不能从参考补足else语义。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob132_always_if2_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob132_always_if2_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob132_always_if2_test.sv)；MIT，固定commit。

原题SHA256：8a3ea8c732f21239cd4141606628d08ad4115da6ed4c16cc2b6ac41f68311cf7

```text

Consider the following adder-subtractor with a zero flag:

  module TopModule (
      input      cpu_overheated,
      output reg shut_off_computer,
      input      arrived,
      input      gas_tank_empty,
      output reg keep_driving
  );

      always @(*) begin
          if (cpu_overheated)
             shut_off_computer = 1;
      end

      always @(*) begin
          if (~arrived)
             keep_driving = ~gas_tank_empty;
      end

  endmodule

Unfortunately, this module has a bug. Implement a new version of this
module that fixes the bug.

```

自动检索：LR008, LR002, LR003；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob132_always_if2.json，完整实际拟消息见messages/Prob132_always_if2__rag.json和__no_rag.json。


LR008，score=3.223432385384224，Sequential Logic (Registers)，L1897-1901，SHA 21c198d95c6a31cf2ed9e901a11384008476b278830e4a0be73c3c5feb192946

```text
Keep work in sequential blocks simple. If a sequential block becomes
sufficiently complicated, consider splitting the combinational logic into a
separate combinational (`always_comb`) block. Ideally, sequential blocks should
contain only a register instantiation, with perhaps a load enable or an
increment.
```


LR002，score=2.909095903096425，Delay Modeling，L1789-1790，SHA f08d2bb9835cd2c97e28e5887e08b5b4a8a22fbf1363bff522ea521583dc5538

```text
Synthesizable design modules must be designed around a zero-delay simulation
methodology. All forms of `#delay`, including `#0`, are not permitted.
```


LR003，score=2.7039884829371292，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 9. Prob032_vector0 — 三位向量拆线

标签：CONFIRMED_CLEAR_SUBSET；原标签：SELECTED_CONDITIONAL / ELIGIBLE。

原依据：明确outv原样输出、o0/o1/o2按位输出；与decoder3的onehot解码、mux8的选择函数不同。没有状态/复位语义缺口。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob032_vector0_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob032_vector0_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob032_vector0_test.sv)；MIT，固定commit。

原题SHA256：86607e1d27d54efeeb53ee5574c6884b1b51ab855b693422cf6c1bfdaba98ca0

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

自动检索：LR018, LR015, LR008；EXACT_REUSE_PRIOR_FROZEN_RESULT；完整18排名/逐词分数/全文见retrieval/Prob032_vector0.json，完整实际拟消息见messages/Prob032_vector0__rag.json和__no_rag.json。


LR018，score=3.7475288712241452，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR008，score=3.394616774574386，Sequential Logic (Registers)，L1897-1901，SHA 21c198d95c6a31cf2ed9e901a11384008476b278830e4a0be73c3c5feb192946

```text
Keep work in sequential blocks simple. If a sequential block becomes
sufficiently complicated, consider splitting the combinational logic into a
separate combinational (`always_comb`) block. Ideally, sequential blocks should
contain only a register instantiation, with perhaps a load enable or an
increment.
```


## 10. Prob064_vector3 — 向量拼接拆分

标签：UNSPECIFIED_CONCAT_SPLIT_ORDER；原标签：SELECTED_CONDITIONAL / ELIGIBLE。

原依据：六个5位输入按列举a..f顺序拼接，末尾二个1，按w/x/y/z顺序拆成32位。参考与列举顺序一致；原文没有显式拼接等式，顺序解释在审阅说明中披露，不写回原题。与历史shift/mux功能不同。

总控后续语义裁决覆盖原条件性解释，见coordinator-semantic-review.md。

[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob064_vector3_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob064_vector3_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob064_vector3_test.sv)；MIT，固定commit。

原题SHA256：ff98e7fba9109a1736b495bc5a2b9fe1c5e8f058e97fe511ecf1cb330c5b1da9

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

自动检索：LR018, LR015, LR003；EXACT_REUSE_PRIOR_FROZEN_RESULT；完整18排名/逐词分数/全文见retrieval/Prob064_vector3.json，完整实际拟消息见messages/Prob064_vector3__rag.json和__no_rag.json。


LR018，score=8.635117229532888，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=5.036393734203968，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=2.969023870581372，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 11. Prob065_7420 — 双四输入NAND

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：两个独立四输入归约NAND，接口齐全。历史ALU含逐位AND但非这两组归约输出，基础门共享不是完整近重复。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob065_7420_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob065_7420_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob065_7420_test.sv)；MIT，固定commit。

原题SHA256：79ffe176455537fa154d36c00c56f14821825c78254e750ea81273e12ec95775

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  p1a
 - input  p1b
 - input  p1c
 - input  p1d
 - input  p2a
 - input  p2b
 - input  p2c
 - input  p2d
 - output p1y
 - output p2y

The 7400-series integrated circuits are a series of digital chips with a
few gates each. The 7420 is a chip with two 4-input NAND gates. The
module should implement the same functionality as the 7420 chip.

```

自动检索：LR018, LR015, LR010；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob065_7420.json，完整实际拟消息见messages/Prob065_7420__rag.json和__no_rag.json。


LR018，score=3.7475288712241452，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR010，score=3.164597955848727，Combinational Logic，L2152-2153，SHA f1044589bb7940ec2cb3d3cd0e6488dcce2a40da913569935f328601dce6cf4f

```text
Do not use three-state logic (`Z` state) to accomplish on-chip logic such as
muxing.
```


## 12. Prob109_fsm1 — 二状态翻转

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / HISTORY_NEAR_DUPLICATE。

原依据：遇in=0翻转、in=1保持，reset输出1；与event_parity输入反相/初值变化同构，保守排除。原文另未明确clk边沿，不补足。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob109_fsm1_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob109_fsm1_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob109_fsm1_test.sv)；MIT，固定commit。

原题SHA256：6c20b60f97687f891524015003e088a65dd2bd450ebcf2499fd2601bde2f404e

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  areset
 - input  in
 - output out

The module should implement a Moore machine with the diagram described
below:

  B (1) --0--> A
  B (1) --1--> B
  A (0) --0--> B
  A (0) --1--> A

It should asynchronously reset into state B if reset if high.

```

自动检索：LR006, LR018, LR015；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob109_fsm1.json，完整实际拟消息见messages/Prob109_fsm1__rag.json和__no_rag.json。


LR006，score=6.132472310619519，Sequential Logic (Registers)，L1818-1820，SHA e21796acf251a073061ee4e103ad61404d82cbafca689dc2df125e2c0df8e647

```text
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.
```


LR018，score=5.1954021019231345，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=4.865177278498858，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


## 13. Prob150_review2015_fsmonehot — 组合FSM方程

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / HISTORY_NEAR_DUPLICATE。

原依据：包含已暴露Prob095四拍shift_ena和Prob096的1101识别子机；组合方程任务形式不同仍实质复用已读结构，保守排除。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob150_review2015_fsmonehot_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob150_review2015_fsmonehot_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob150_review2015_fsmonehot_test.sv)；MIT，固定commit。

原题SHA256：9c02d1cfaafd494a2696d041d713358e9df12ef080c8de0c352cee109417a1ad

```text
I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  d
 - input  done_counting
 - input  ack
 - input  state (10 bits)
 - output B3_next
 - output S_next
 - output S1_next
 - output Count_next
 - output Wait_next
 - output done
 - output counting
 - output shift_ena

The module should implement the following Moore state machine with 3
input (d, done_counting, ack) and 3 outputs (shift_ena, counting, done).
Unless otherwise stated in the diagram below, assume outputs are 0 and
inputs are don't cares.

state   (output)      --input--> next state
-------------------------------------------
  S     ()            --d=0--> S
  S     ()            --d=1--> S1
  S1    ()            --d=0--> S
  S1    ()            --d=1--> S11
  S11   ()            --d=0--> S110
  S11   ()            --d=1--> S11
  S110  ()            --d=0--> S
  S110  ()            --d=1--> B0
  B0    (shift_ena=1) --(always go to next cycle)--> B1
  B1    (shift_ena=1) --(always go to next cycle)--> B2
  B2    (shift_ena=1) --(always go to next cycle)--> B3
  B3    (shift_ena=1) --(always go to next cycle)--> Count
  Count (counting=1)  --done_counting=0--> Count
  Count (counting=1)  --done_counting=1--> Wait
  Wait  (done=1)      --ack=0--> Wait
  Wait  (done=1)      --ack=1--> S

At reset, the state machine starts in state "S". Derive next-state logic
equations and output logic equations by inspection assuming the following
one-hot encoding is used: (S, S1, S11, S110, B0, B1, B2, B3, Count, Wait)
= (10'b0000000001, 10'b0000000010, 10'b0000000100, ... , 10'b1000000000)

Derive state transition and output logic equations by inspection assuming
a one-hot encoding. Implement only the state transition logic and output
logic (the combinational logic portion) for this state machine.

Write code that generates the following signals:

 - B3_next -- Assert when next-state is B3 state
 - S_next -- Assert when next-state is S state
 - S1_next -- Assert when next-state is S1 state
 - Count_next -- Assert when next-state is Count state
 - Wait_next -- Assert when next-state is Wait state
 - done -- output logic
 - counting -- output logic
 - shift_ena -- output logic

```

自动检索：LR006, LR018, LR010；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob150_review2015_fsmonehot.json，完整实际拟消息见messages/Prob150_review2015_fsmonehot__rag.json和__no_rag.json。


LR006，score=11.304752928463838，Sequential Logic (Registers)，L1818-1820，SHA e21796acf251a073061ee4e103ad61404d82cbafca689dc2df125e2c0df8e647

```text
Sequential statements for state assignments should only contain reset values and
a next-state to state assignment, use a separate combinational-only block to
generate that next-state value.
```


LR018，score=6.351972316613687，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR010，score=5.425544321663798，Combinational Logic，L2152-2153，SHA f1044589bb7940ec2cb3d3cd0e6488dcce2a40da913569935f328601dce6cf4f

```text
Do not use three-state logic (`Z` state) to accomplish on-chip logic such as
muxing.
```


## 14. Prob044_vectorgates — 向量逻辑门

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：同时给逐位OR、逻辑OR、按明确次序NOT拼接；与历史ALU单项OR有原语交叉，但完整多输出契约不同。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob044_vectorgates_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob044_vectorgates_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob044_vectorgates_test.sv)；MIT，固定commit。

原题SHA256：ca7e990ab01903f606c956d8af8fb9faf01adf063847560d23e3d99fc10968a7

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a              (3 bits)
 - input  b              (3 bits)
 - output out_or_bitwise (3 bits)
 - output out_or_logical
 - output out_not        (6 bits)

Implement a module with two 3-bit inputs that computes the bitwise-OR of
the two vectors, the logical-OR of the two vectors, and the inverse (NOT)
of both vectors. Place the inverse of b in the upper half of out_not
(i.e., bits [5:3]), and the inverse of a in the lower half.

```

自动检索：LR018, LR015, LR003；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob044_vectorgates.json，完整实际拟消息见messages/Prob044_vectorgates__rag.json和__no_rag.json。


LR018，score=5.1954021019231345，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=2.969023870581372，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 15. Prob042_vector4 — 符号扩展

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：8→32位符号复制，接口和示例完整；历史signedcmp8的比较结果不同，非仅宽度变体。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob042_vector4_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob042_vector4_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob042_vector4_test.sv)；MIT，固定commit。

原题SHA256：8d2ef1d00ecc693bcf3b1438fb20676ed098d3dd52660618f78a0a02a225d7da

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in  (8  bits)
 - output out (32 bits)

One common place to see a replication operator is when sign-extending a
smaller number to a larger one, while preserving its signed value. This
is done by replicating the sign bit (the most significant bit) of the
smaller number to the left. For example, sign-extending 4'b0101 (5) to 8
bits results in 8'b00000101 (5), while sign-extending 4'b1101 (-3) to 8
bits results in 8'b11111101 (-3). Implement a module that sign-extends an
8-bit number to 32 bits. This requires a concatenation of 24 copies of
the sign bit (i.e., replicate bit[7] 24 times) followed by the 8-bit
number itself.

```

自动检索：LR018, LR015, LR016；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob042_vector4.json，完整实际拟消息见messages/Prob042_vector4__rag.json和__no_rag.json。


LR018，score=6.351972316613688，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR016，score=3.1643792470478207，Case Statements，L2238-2240，SHA 9d9505478f985c8e35f7e7b43505c037c57c12ebb1b27efdf4916f9a78d11dfd

```text
Use `case` if wildcard operator behavior is not needed.
Use `case inside` if wildcard operator behavior is needed.
Use `casez` if wildcard operator behavior is needed and Verilog-2001 compatibility is required.
```


## 16. Prob005_notgate — NOT门

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：完整一位反相契约；历史集合没有该完整独立任务。简单程度不作为入选/排除依据。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob005_notgate_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob005_notgate_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob005_notgate_test.sv)；MIT，固定commit。

原题SHA256：0dcc1f15aa03789c4b4fcaa87aaea9f1f6c6618bb65aaf12db601c9ccda49cc4

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in
 - output out

The module should implement a NOT gate.

```

自动检索：LR018, LR015, LR003；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob005_notgate.json，完整实际拟消息见messages/Prob005_notgate__rag.json和__no_rag.json。


LR018，score=3.7475288712241452，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=3.404362645465794，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=2.969023870581372，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


## 17. Prob074_ece241_2014_q4 — 三反馈寄存器

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：三支XOR/AND/OR反馈及NOR输出，初态全0与posedge明确；其中一支与event_parity共享原语但完整三状态位系统不同。初始化声明可在单模块表达；可综合性平台适配未校准。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob074_ece241_2014_q4_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob074_ece241_2014_q4_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob074_ece241_2014_q4_test.sv)；MIT，固定commit。

原题SHA256：0657a3b595a3caa3a20be1d59d028a757ab823cc4acc059f9a7543f687bc1346

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  x
 - output z

The module should implement a finite state machine with the following
behavior. Input x goes to three different two-input gates: an XOR, an
AND, and a OR gate. Each of the three gates is connected to the input of
a D flip-flop and then the flip-flop outputs all go to a three-input
NOR gate, whose output is Z. The second input of the XOR is its corresponding
flip-flop's output, the second input of the AND is its corresponding
flip-flop's complemented output, and finally the second input of the OR
is its corresponding flip-flop's complementary output.

Assume that the D flip-flops are initially reset to zero before the
machine begins. Assume all sequential logic is triggered on the positive
edge of the clock.

```

自动检索：LR010, LR015, LR018；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob074_ece241_2014_q4.json，完整实际拟消息见messages/Prob074_ece241_2014_q4__rag.json和__no_rag.json。


LR010，score=9.959461687459928，Combinational Logic，L2152-2153，SHA f1044589bb7940ec2cb3d3cd0e6488dcce2a40da913569935f328601dce6cf4f

```text
Do not use three-state logic (`Z` state) to accomplish on-chip logic such as
muxing.
```


LR015，score=8.71151230266317，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR018，score=8.635117229532888，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


## 18. Prob043_vector5 — 25项两两比较

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：5标量的全对XNOR矩阵及位序明确；与历史signedcmp8数值大小比较/单一parity输出不同。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob043_vector5_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob043_vector5_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob043_vector5_test.sv)；MIT，固定commit。

原题SHA256：0ef3f6be0cd42d8fe1d4a6c8d1a4b6972862a4a0833afcf85f81f8e33b01d2ce

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - input  c
 - input  d
 - input  e
 - output out (25 bits)

Implement a module that given five 1-bit signals (a, b, c, d, and e),
compute all 25 pairwise one-bit comparisons in the 25-bit output vector.
The output should be 1 if the two bits being compared are equal. Example:
out[24] = ~a ^ a; out[23] = ~a ^ b; out[22] = ~a ^ c; ...
out[ 1] = ~e ^ d; out[ 0] = ~e ^ e.

```

自动检索：LR015, LR003, LR018；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob043_vector5.json，完整实际拟消息见messages/Prob043_vector5__rag.json和__no_rag.json。


LR015，score=4.865177278498858，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=4.418692918927001，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```


LR018，score=3.7475288712241452，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


## 19. Prob071_always_casez — 优先编码器

标签：HISTORY_OR_SPEC_EXCLUDED；原标签：EXCLUDED / HISTORY_NEAR_DUPLICATE。

原依据：与历史encoder4/leadingzero8为优先位置编码族，仅宽度/扫描方向/valid输出变化，保守排除。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob071_always_casez_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob071_always_casez_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob071_always_casez_test.sv)；MIT，固定commit。

原题SHA256：bd14f7fa05e5db09dc82db362762860b4f092f069b989eb40dcc6038877ca86d

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in  (8 bits)
 - output pos (3 bits)

The module should implement a priority encoder for an 8-bit input. Given
an 8-bit vector, the output should report the first (least significant)
bit in the vector that is 1. Report zero if the input vector has no bits
that are high. For example, the input 8'b10010000 should output 3'd4,
because bit[4] is first bit that is high.

```

自动检索：LR015, LR018, LR002；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob071_always_casez.json，完整实际拟消息见messages/Prob071_always_casez__rag.json和__no_rag.json。


LR015，score=6.908264758219886，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR018，score=5.1954021019231345，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR002，score=4.847378060351743，Delay Modeling，L1789-1790，SHA f08d2bb9835cd2c97e28e5887e08b5b4a8a22fbf1363bff522ea521583dc5538

```text
Synthesizable design modules must be designed around a zero-delay simulation
methodology. All forms of `#delay`, including `#0`, are not permitted.
```


## 20. Prob127_lemmings1 — Lemmings方向机

标签：OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET；原标签：ELIGIBLE_NOT_SELECTED_FIXED_CAP / ELIGIBLE。

原依据：两输入按当前方向响应碰撞，同时碰撞翻向，posedge异步高reset到向左。与event_parity无状态依赖选择输入、单条件翻转不同；非旧ve_fsm三状态图。


[原题](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob127_lemmings1_prompt.txt) / [参考](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob127_lemmings1_ref.sv) / [测试](https://github.com/NVlabs/verilog-eval/blob/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob127_lemmings1_test.sv)；MIT，固定commit。

原题SHA256：896214e584d27c9d50980edbff2439df33e817f89c4624d9cc1115ab1955276d

```text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  areset
 - input  bump_left
 - input  bump_right
 - output walk_left
 - output walk_right

The module should implement a simple game called Lemmings which involves
critters with fairly simple brains. So simple that we are going to model
it using a finite state machine. In the Lemmings' 2D world, Lemmings can
be in one of two states: walking left (walk_left is 1) or walking right
(walk_right is 1). It will switch directions if it hits an obstacle. In
particular, if a Lemming is bumped on the left (by receiving a 1 on
bump_left), it will walk right. If it's bumped on the right (by receiving
a 1 on bump_right), it will walk left. If it's bumped on both sides at
the same time, it will still switch directions.

The module should implement a Moore state machine with two states, two
inputs, and one output (internal to the module) that models this
behaviour. areset is positive edge triggered asynchronous resetting the
Lemming machine to walk left. Assume all sequential logic is triggered on
the positive edge of the clock.

```

自动检索：LR018, LR015, LR003；NEW_FROZEN_AUTOMATIC_RETRIEVAL；完整18排名/逐词分数/全文见retrieval/Prob127_lemmings1.json，完整实际拟消息见messages/Prob127_lemmings1__rag.json和__no_rag.json。


LR018，score=8.94293097314728，Case Statements，L2245-2252，SHA 38b511f542f8fcb62c5ad046b40e95a8c569d5e5b69bdce9dbe2cc6e393640e9

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


LR015，score=7.857028088115966，Case Statements，L2189-2192，SHA 671cab8965910cd22aa4aa60fb141c20ee77102e6da34dd8c28e743cf5ec15e0

```text
  - a `default:` statement is **always** included in order to avoid accidental
  inference of latches, even if all cases are covered. In simulation, a case
  expression that evaluates to `X` will not match any case and will behave as a
  latch, leading to different behavior than synthesis if no default is specified.
```


LR003，score=6.199189697035746，Sequential Logic (Latches)，L1802-1803，SHA bebab74d9159028626ec42336b8a11d2d3850005988ffd16e22d4d44f7953c7f

```text
If you must use a latch, use `always_latch` over `always`, and use non-blocking
assignments (`<=`). Never use blocking assignments (`=`).
```
