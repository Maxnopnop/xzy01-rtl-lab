# 30题原始提示词全文

以下逐题正文来自冻结上游文件；中文说明另见 USER_REVIEW.md，未写入请求。权威字节以链接原文件及SHA为准。

## 1. Prob055_conditional

[原文件](originals/dataset_spec-to-rtl/Prob055_conditional_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_prompt.txt)

SHA256 `a4cb1a6391988c0c0661808b8bafb625160c70dab00c917bc970be65aa9b34c7`

````text

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


````

## 2. Prob142_lemmings2

[原文件](originals/dataset_spec-to-rtl/Prob142_lemmings2_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob142_lemmings2_prompt.txt)

SHA256 `dff9caac89ffa86372042cda54ca68f8388a2ca4f33f20092c3ef1db904bf466`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  areset
 - input  bump_left
 - input  bump_right
 - input  ground
 - output walk_left
 - output walk_right
 - output aaah

The game Lemmings involves critters with fairly simple brains. So simple
that we are going to model it using a finite state machine. In the
Lemmings' 2D world, Lemmings can be in one of two states: walking left
(walk_left is 1) or walking right (walk_right is 1). It will switch
directions if it hits an obstacle. In particular, if a Lemming is bumped
on the left (by receiving a 1 on bump_left), it will walk right. If it's
bumped on the right (by receiving a 1 on bump_right), it will walk left.
If it's bumped on both sides at the same time, it will still switch
directions.

In addition to walking left and right and changing direction when bumped,
when ground=0, the Lemming will fall and say "aaah!". When the ground
reappears (ground=1), the Lemming will resume walking in the same
direction as before the fall. Being bumped while falling does not affect
the walking direction, and being bumped in the same cycle as ground
disappears (but not yet falling), or when the ground reappears while
still falling, also does not affect the walking direction.

Implement a Moore state machine that models this behaviour. areset is
positive edge triggered asynchronous reseting the Lemming machine to walk
left. Assume all sequential logic is triggered on the positive edge of
the clock.


````

## 3. Prob124_rule110

[原文件](originals/dataset_spec-to-rtl/Prob124_rule110_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_prompt.txt)

SHA256 `3149f58c7fa9a5c9ac21216994a268ea5b143a9c0cd56872f8ea7835f10ecdd3`

````text

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


````

## 4. Prob016_m2014_q4j

[原文件](originals/dataset_spec-to-rtl/Prob016_m2014_q4j_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob016_m2014_q4j_prompt.txt)

SHA256 `bdc58ca32db81e53addd16cc5cd671c2d1f839591317ebe7174fb16b9ec23dc5`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  x   (4 bits)
 - input  y   (4 bits)
 - output sum (5 bits)

Implement a 4-bit adder with full adders. The output sum should include
the overflow bit.


````

## 5. Prob135_m2014_q6b

[原文件](originals/dataset_spec-to-rtl/Prob135_m2014_q6b_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob135_m2014_q6b_prompt.txt)

SHA256 `02da5df3fa54157b706f445bb1e6a0d078c9c90b7af01218e0567187bb4d9d2d`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  y (3 bits)
 - input  w
 - output Y1

The module should implement the state machine shown below:

  A (0) --0--> B
  A (0) --1--> A
  B (0) --0--> C
  B (0) --1--> D
  C (0) --0--> E
  C (0) --1--> D
  D (0) --0--> F
  D (0) --1--> A
  E (1) --0--> E
  E (1) --1--> D
  F (1) --0--> C
  F (1) --1--> D

The FSM should be implemented using three flip-flops and state codes
y = 000, 001, ..., 101 for states A, B, ..., F, respectively. Implement
just the next-state logic for y[1]. The output Y1 is y[1].


````

## 6. Prob026_alwaysblock1

[原文件](originals/dataset_spec-to-rtl/Prob026_alwaysblock1_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob026_alwaysblock1_prompt.txt)

SHA256 `6eae7df079dcd42bd6dedd42895a6ca4dae7c52112a894c20b17b0febd071924`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - output out_assign
 - output out_alwaysblock

The module should implement an AND gate using both an assign statement
and a combinational always block.


````

## 7. Prob139_2013_q2bfsm

[原文件](originals/dataset_spec-to-rtl/Prob139_2013_q2bfsm_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob139_2013_q2bfsm_prompt.txt)

SHA256 `fd660ca7619ae0a5d8ebf262aadb5cb44555d509b453cf5d630204618d0a9bba`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  resetn
 - input  x
 - input  y
 - output f
 - output g

Consider a finite state machine that is used to control some type of
motor. The FSM has inputs x and y, which come from the motor, and
produces outputs f and g, which control the motor. There is also a clock
input called clk and a reset input (synchronous, active low) called
resetn. The FSM has to work as follows. As long as the reset input is
asserted, the FSM stays in a beginning state, called state A. When the
reset signal is de-asserted, then after the next clock edge the FSM has
to set the output f to 1 for one clock cycle. Then, the FSM has to
monitor the x input. When x has produced the values 1, 0, 1 in three
successive clock cycles, then g should be set to 1 on the following clock
cycle. While maintaining g = 1 the FSM has to monitor the y input. If y
has the value 1 within at most two clock cycles, then the FSM should
maintain g = 1 permanently (that is, until reset). But if y does not
become 1 within two clock cycles, then the FSM should set g = 0
permanently (until reset). Assume all sequential logic is triggered on
the positive edge of the clock.


````

## 8. Prob020_mt2015_eq2

[原文件](originals/dataset_spec-to-rtl/Prob020_mt2015_eq2_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob020_mt2015_eq2_prompt.txt)

SHA256 `07d916e51b5866b561cb5f9df738156e61eb5b517cd5b52cd3f92acfc4979113`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  A (2 bits)
 - input  B (2 bits)
 - output z

The module should implement a circuit that has two 2-bit inputs A[1:0]
and B[1:0], and produces an output z. The value of z should be 1 if A =
B, otherwise z should be 0.


````

## 9. Prob112_always_case2

[原文件](originals/dataset_spec-to-rtl/Prob112_always_case2_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob112_always_case2_prompt.txt)

SHA256 `6a17eb818d48dab63be542a115dee4223fb7bd480ea9a2161ca8724aab15cc82`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in  (4 bits)
 - output pos (2 bits)

The module should implement a priority encoder. A priority encoder is a
combinational circuit that, when given an input bit vector, outputs the
position of the first 1 bit in the vector. For example, a 8-bit priority
encoder given the input 8'b10010000 would output 3'd4, because bit[4] is
first bit that is high. Build a 4-bit priority encoder. For this problem,
if none of the input bits are high (i.e., input is zero), output zero.
Note that a 4-bit number has 16 possible combinations.


````

## 10. Prob010_mt2015_q4a

[原文件](originals/dataset_spec-to-rtl/Prob010_mt2015_q4a_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob010_mt2015_q4a_prompt.txt)

SHA256 `ddff8d7fc684321656bfa87bc8c428cf7044d2a2e4de8dc4be1b2ec6d9f50281`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  x
 - input  y
 - output z

The module should implement the boolean function z = (x^y) & x.


````

## 11. Prob108_rule90

[原文件](originals/dataset_spec-to-rtl/Prob108_rule90_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob108_rule90_prompt.txt)

SHA256 `4630998fdc4009e15dcac0712ac56392621eb01a24ef5de09417f99fcf9b1508`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk,
 - input  load,
 - input  data (512 bits)
 - output q    (512 bits)

The module should implement Rule 90, a one-dimensional cellular automaton
with interesting properties. The rules are simple. There is a
one-dimensional array of cells (on or off). At each time step, the next
state of each cell is the XOR of the cell's two current neighbours:

  Left | Center | Right | Center's next state
  1    | 1      | 1     | 0
  1    | 1      | 0     | 1
  1    | 0      | 1     | 0
  1    | 0      | 0     | 1
  0    | 1      | 1     | 1
  0    | 1      | 0     | 0
  0    | 0      | 1     | 1
  0    | 0      | 0     | 0

In this circuit, create a 512-cell system (q[511:0]), and advance by one
time step each clock cycle. The load input indicates the state of the
system should be loaded with data[511:0]. Assume the boundaries (q[-1]
and q[512]) are both zero (off). Assume all sequential logic is triggered
on the positive edge of the clock.


````

## 12. Prob140_fsm_hdlc

[原文件](originals/dataset_spec-to-rtl/Prob140_fsm_hdlc_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob140_fsm_hdlc_prompt.txt)

SHA256 `8cccb78555aa84398c381d96b7385e3eee9b34333b7bc5807e6afc38c216eead`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  in
 - output disc
 - output flag
 - output err

Synchronous HDLC framing involves decoding a continuous bit stream of
data to look for bit patterns that indicate the beginning and end of
frames (packets). Seeing exactly 6 consecutive 1s (i.e., 01111110) is a
"flag" that indicate frame boundaries. To avoid the data stream from
accidentally containing "flags", the sender inserts a zero after every 5
consecutive 1s which the receiver must detect and discard. We also need
to signal an error if there are 7 or more consecutive 1s. Create a
Moore-type finite state machine to recognize these three sequences:

  (1) 0111110: Signal a bit needs to be discarded (disc).
  (2) 01111110: Flag the beginning/end of a frame (flag).
  (3) 01111111...: Error (7 or more 1s) (err).

When the FSM is reset, it should be in a state that behaves as though the
previous input were 0. The reset signal is active high synchronous. The
output signals should be asserted for a complete cycle beginning on the
clock cycle after the condition occurs. Assume all sequential
logic is triggered on the positive edge of the clock.


````

## 13. Prob137_fsm_serial

[原文件](originals/dataset_spec-to-rtl/Prob137_fsm_serial_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob137_fsm_serial_prompt.txt)

SHA256 `fe3610ac99739ba5073e7eee30fcf190dea64cfbd7d564398b45deadd987b826`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  in
 - output done

In many (older) serial communications protocols, each data byte is sent
along with a start bit and a stop bit, to help the receiver delimit bytes
from the stream of bits. One common scheme is to use one start bit (0), 8
data bits, and 1 stop bit (1). The line is also at logic 1 when nothing
is being transmitted (idle).

Implement a finite state machine that will identify when bytes have been
correctly received when given a stream of bits. It needs to identify the
start bit, wait for all 8 data bits, then verify that the stop bit was
correct. If the stop bit does not appear when expected, the FSM must wait
until it finds a stop bit before attempting to receive the next byte.
Include a active-high synchronous reset. Note that the serial protocol
sends the least significant bit first.

Assume all sequential logic is triggered on the positive edge of the
clock.


````

## 14. Prob129_ece241_2013_q8

[原文件](originals/dataset_spec-to-rtl/Prob129_ece241_2013_q8_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob129_ece241_2013_q8_prompt.txt)

SHA256 `84b421b6b8b363ad0046d586dc5c5460a8d21e5e3994a78b2f0cdcdc9ee0d7c7`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  aresetn
 - input  x
 - output z

The module should implement a Mealy-type finite state machine that
recognizes the sequence "101" on an input signal named x. Your FSM should
have an output signal, z, that is asserted to logic-1 when the "101"
sequence is detected. Your FSM should also have a negative edge triggered
asynchronous reset. You may only have 3 states in your state machine.
Your FSM should recognize overlapping sequences. Assume all sequential
logic is triggered on the positive edge of the clock.


````

## 15. Prob153_gshare

[原文件](originals/dataset_spec-to-rtl/Prob153_gshare_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob153_gshare_prompt.txt)

SHA256 `dfac7601e96bdcfacd43944bfcdd5c5677a4d9a68f56532a0608b525f54c36b4`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  areset

 - input  predict_valid,
 - input  predict_pc (7 bits)
 - output predict_taken
 - output predict_history (7 bits)

 - input  train_valid
 - input  train_taken
 - input  train_mispredicted
 - input  train_history (7 bits)
 - input  train_pc (7 bits)

The module should implement a gshare branch predictor with 7-bit pc and
7-bit global history, hashed (using xor) into a 7-bit index. This index
accesses a 128-entry table of two-bit saturating counters. The branch
predictor should contain a 7-bit global branch history register. The
branch predictor has two sets of interfaces: One for doing predictions
and one for doing training. The prediction interface is used in the
processor's Fetch stage to ask the branch predictor for branch direction
predictions for the instructions being fetched. Once these branches
proceed down the pipeline and are executed, the true outcomes of the
branches become known. The branch predictor is then trained using the
actual branch direction outcomes.

When a branch prediction is requested (predict_valid = 1) for a given pc,
the branch predictor produces the predicted branch direction and state of
the branch history register used to make the prediction. The branch
history register is then updated (at the next positive clock edge) for
the predicted branch.

When training for a branch is requested (train_valid = 1), the branch
predictor is told the pc and branch history register value for the branch
that is being trained, as well as the actual branch outcome and whether
the branch was a misprediction (needing a pipeline flush). Update the
pattern history table (PHT) to train the branch predictor to predict this
branch more accurately next time. In addition, if the branch being
trained is mispredicted, also recover the branch history register to the
state immediately after the mispredicting branch completes execution.

If training for a misprediction and a prediction (for a different,
younger instruction) occurs in the same cycle, both operations will want
to modify the branch history register. When this happens, training takes
precedence, because the branch being predicted will be discarded anyway.
If training and prediction of the same PHT entry happen at the same time,
the prediction sees the PHT state before training because training only
modifies the PHT at the next positive clock edge. The following timing
diagram shows the timing when training and predicting PHT entry 0 at the
same time. The training request at cycle 4 changes the PHT entry state in
cycle 5, but the prediction request in cycle 4 outputs the PHT state at
cycle 4, without considering the effect of the training request in cycle
4. Reset is asynchronous active-high.

Assume all sequential logic is triggered on the positive edge of the
clock.


````

## 16. Prob048_m2014_q4c

[原文件](originals/dataset_spec-to-rtl/Prob048_m2014_q4c_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob048_m2014_q4c_prompt.txt)

SHA256 `01faebfe50b95f304c326dd2f7cdc3cd67c3210f69a2de3fe8df02b3edaffb05`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  d
 - input  r
 - output q

The module should implement a simple D flip flop with active high
synchronous reset (reset output to 0).


````

## 17. Prob116_m2014_q3

[原文件](originals/dataset_spec-to-rtl/Prob116_m2014_q3_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob116_m2014_q3_prompt.txt)

SHA256 `9c40c9be5f741d9678898b4e27c58737aed85873059f258eb3027706515f46ed`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  x (4 bits)
 - output f

The module should implement the function f shown in the Karnaugh map
below. d is don't-care, which means you may choose to output whatever
value is convenient.

                x[1]x[2]
  x[3]x[4]   00  01  11  10
        00 | d | 0 | d | d |
        01 | 0 | d | 1 | 0 |
        11 | 1 | 1 | d | d |
        10 | 1 | 1 | 0 | d |


````

## 18. Prob025_reduction

[原文件](originals/dataset_spec-to-rtl/Prob025_reduction_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob025_reduction_prompt.txt)

SHA256 `0734b084119e62e858a877d0cb729da5d28f503fcb40c93a5c82a6fa75051d2d`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in     (8 bits)
 - output parity

Parity checking is often used as a simple method of detecting errors when
transmitting data through an imperfect channel. The module should compute
a parity bit for an 8-bit byte (which will add a 9th bit to the byte). We
will use "even" parity, where the parity bit is just the XOR of all 8
data bits.


````

## 19. Prob138_2012_q2fsm

[原文件](originals/dataset_spec-to-rtl/Prob138_2012_q2fsm_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob138_2012_q2fsm_prompt.txt)

SHA256 `118be360b0c8dea9915cf4520b01886243c6df6c9e2301ed66abf8b6eab04147`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  w
 - output z

The module should implement the state machine shown below:

  A (0) --1--> B
  A (0) --0--> A
  B (0) --1--> C
  B (0) --0--> D
  C (0) --1--> E
  C (0) --0--> D
  D (0) --1--> F
  D (0) --0--> A
  E (1) --1--> E
  E (1) --0--> D
  F (1) --1--> C
  F (1) --0--> D

Reset resets into state A and is synchronous active-high. Assume all
sequential logic is triggered on the positive edge of the clock.

Use separate always blocks for the state table and the state flip-flops.
Describe the FSM output, which is called _z_, using either continuous
assignment statement(s) or an always block (at your discretion). Assign
any state codes that you wish to use.


````

## 20. Prob130_circuit5

[原文件](originals/dataset_spec-to-rtl/Prob130_circuit5_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob130_circuit5_prompt.txt)

SHA256 `e60c6bc1414689917b8f7b58a24d59187c794e10dd6801069b60f096c76e1303`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a (4 bits)
 - input  b (4 bits)
 - input  c (4 bits)
 - input  d (4 bits)
 - input  e (4 bits)
 - output q (4 bits)

The module should implement a combinational circuit. Read the simulation
waveforms to determine what the circuit does, then implement it.

  time  a  b  c  d  e  q
  0ns   x  x  x  x  x  x
  5ns   x  x  x  x  x  x
  10ns  x  x  x  x  x  x
  15ns  a  b  0  d  e  b
  20ns  a  b  1  d  e  e
  25ns  a  b  2  d  e  a
  30ns  a  b  3  d  e  d
  35ns  a  b  4  d  e  f
  40ns  a  b  5  d  e  f
  45ns  a  b  6  d  e  f
  50ns  a  b  7  d  e  f
  55ns  a  b  8  d  e  f
  60ns  a  b  9  d  e  f
  65ns  a  b  a  d  e  f
  70ns  a  b  b  d  e  f
  75ns  a  b  c  d  e  f
  80ns  a  b  d  d  e  f
  85ns  a  b  e  d  e  f
  90ns  a  b  f  d  e  f


````

## 21. Prob011_norgate

[原文件](originals/dataset_spec-to-rtl/Prob011_norgate_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob011_norgate_prompt.txt)

SHA256 `0d5777800631b73e5922ccec5061f76321cabe9ad68b770d371bf3f26a51d505`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - output out

The module should implement a NOR gate.


````

## 22. Prob013_m2014_q4e

[原文件](originals/dataset_spec-to-rtl/Prob013_m2014_q4e_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob013_m2014_q4e_prompt.txt)

SHA256 `c4adcffee7da43aa1ec11ae8ba93095a5e34f1ffade2418c05f2a4ef3075d9a4`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  in1
 - input  in2
 - output out

The module should implement a 2-input NOR gate.


````

## 23. Prob107_fsm1s

[原文件](originals/dataset_spec-to-rtl/Prob107_fsm1s_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob107_fsm1s_prompt.txt)

SHA256 `9b7597650973057aba09bff1a801614fc9b4f31ed40d6d85e0396dc600abe4a8`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  in
 - output out

Implement the following Moore state machine with two states, one input,
and one output. The reset state is B and reset is active-high
synchronous.

  B (out=1) --in=0--> A
  B (out=1) --in=1--> B
  A (out=0) --in=0--> B
  A (out=0) --in=1--> A


````

## 24. Prob072_thermostat

[原文件](originals/dataset_spec-to-rtl/Prob072_thermostat_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob072_thermostat_prompt.txt)

SHA256 `b99d5c7402c3d59b35c3396da199442e9fea075d0e31dd703b901ae97b445ae1`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  mode
 - input  too_cold
 - input  too_hot
 - input  fan_on
 - output heater
 - output aircon
 - output fan

The module should implement a heating/cooling thermostat controller which
controls both a heater (during winter) and an air conditioner (during
summer). The module should on and off the heater, air conditioning, and
blower fan as appropriate. The thermostat can be in one of two modes:
heating (mode = 1) and cooling (mode = 0). In heating mode, turn the
heater on when it is too cold (too_cold = 1) but do not use the air
conditioner. In cooling mode, turn the air conditioner on when it is too
hot (too_hot = 1), but do not turn on the heater. When the heater or air
conditioner are on, also turn on the fan to circulate the air. In
addition, the user can also request the fan to turn on (fan_on = 1), even
if the heater and air conditioner are off.


````

## 25. Prob090_circuit1

[原文件](originals/dataset_spec-to-rtl/Prob090_circuit1_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob090_circuit1_prompt.txt)

SHA256 `9ad1e640469124039c742f4486200880371f3d6ccf7736fbd7dc33791ccd3c49`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  a
 - input  b
 - output q

The module should implement a combinational circuit. Read the simulation
waveforms to determine what the circuit does, then implement it.

  time  a  b  q
  0ns   0  0  0
  5ns   0  0  0
  10ns  0  0  0
  15ns  0  0  0
  20ns  0  0  0
  25ns  0  1  0
  30ns  0  1  0
  35ns  1  0  0
  40ns  1  0  0
  45ns  1  1  1
  50ns  1  1  1
  55ns  0  0  0
  60ns  0  0  0
  65ns  0  1  0
  70ns  0  1  0
  75ns  1  0  0
  80ns  1  0  0
  85ns  1  1  1
  90ns  1  1  1


````

## 26. Prob069_truthtable1

[原文件](originals/dataset_spec-to-rtl/Prob069_truthtable1_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob069_truthtable1_prompt.txt)

SHA256 `2131087a44ad7f328bafcb1f1b0809c7ccaaaf6bdeca9b51398ef9203c705da2`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  x3
 - input  x2
 - input  x1
 - output f

The module should implement a combinational circuit for the following
truth table:

  x3 | x2 | x1 | f
  0  | 0  | 0  | 0
  0  | 0  | 1  | 0
  0  | 1  | 0  | 1
  0  | 1  | 1  | 1
  1  | 0  | 0  | 0
  1  | 0  | 1  | 1
  1  | 1  | 0  | 0
  1  | 1  | 1  | 1


````

## 27. Prob133_2014_q3fsm

[原文件](originals/dataset_spec-to-rtl/Prob133_2014_q3fsm_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob133_2014_q3fsm_prompt.txt)

SHA256 `b78ad94474c88f937088cdf4fb5a2c1aa83fcd065e20de3d3ed84f77f625bfbf`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  s
 - input  w
 - output z

The module should implement a finite state machine with inputs s and w.
Assume that the FSM begins in a reset state called A, as depicted below.
The FSM remains in state A as long as s = 0, and it moves to state B when
s = 1. Once in state B the FSM examines the value of the input w in the
next three clock cycles. If w = 1 in exactly two of these clock cycles,
then the FSM has to set an output z to 1 in the following clock cycle.
Otherwise z has to be 0. The FSM continues checking w for the next three
clock cycles, and so on. Use as few states as possible. Note that the s
input is used only in state A, so you need to consider just the w input.
Assume reset is active high synchronous. Assume all sequential logic is
triggered on the positive edge of the clock.


````

## 28. Prob128_fsm_ps2

[原文件](originals/dataset_spec-to-rtl/Prob128_fsm_ps2_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob128_fsm_ps2_prompt.txt)

SHA256 `59ee508515a6b2113e46369feb8e4c34f7e71881a1c152ad6a722ee0ba560a0b`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  in (8 bits)
 - output done

The PS/2 mouse protocol sends messages that are three bytes long.
However, within a continuous byte stream, it's not obvious where messages
start and end. The only indication is that the first byte of each three
byte message always has in[3]=1 (but in[3] of the other two bytes may be
1 or 0 depending on data).

The module should implement a finite state machine that will search for
message boundaries when given an input byte stream. The algorithm we'll
use is to discard bytes until we see one with in[3]=1. We then assume
that this is byte 1 of a message, and signal the receipt of a message
once all 3 bytes have been received (done). The FSM should signal done in
the cycle immediately after the third byte of each message was
successfully received. Reset should be active high synchronous. Assume
all sequential logic is triggered on the positive edge of the clock.


````

## 29. Prob053_m2014_q4d

[原文件](originals/dataset_spec-to-rtl/Prob053_m2014_q4d_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob053_m2014_q4d_prompt.txt)

SHA256 `156b0927a00b17a96fef04c7bf2c331b5f8028aac9243115acad3a4473a4b6ef`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  in
 - output out

The module should implement the following circuit: A D flip-flop takes as
input the output of a two-input XOR. The flip-flop is positive edge
triggered by clk, but there is no reset. The XOR takes as input 'in'
along with the output 'out' of the flip-flop.


````

## 30. Prob058_alwaysblock2

[原文件](originals/dataset_spec-to-rtl/Prob058_alwaysblock2_prompt.txt) · [固定commit来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob058_alwaysblock2_prompt.txt)

SHA256 `8332e8ca609d6e36cce74d514ec19ba122bfb23fa6c25d0242ba9f1dcc37bfbe`

````text

I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  a
 - input  b
 - output out_assign
 - output out_always_comb
 - output out_always_ff

The module should implement an XOR gate three ways, using an assign
statement (output out_assign), a combinational always block (output
out_always_comb), and a clocked always block (output out_always_ff). Note
that the clocked always block produces a different circuit from the other
two: There is a flip- flop so the output is delayed. Assume all
sequential logic is triggered on the positive edge of the clock.


````
