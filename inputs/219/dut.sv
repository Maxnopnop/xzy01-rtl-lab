module TopModule (
  input  logic        d,
  input  logic        done_counting,
  input  logic        ack,
  input  logic [9:0]  state,
  output logic        B3_next,
  output logic        S_next,
  output logic        S1_next,
  output logic        Count_next,
  output logic        Wait_next,
  output logic        done,
  output logic        counting,
  output logic        shift_ena
);

  // State one-hot assignments for clarity
  // state[0]: S      0000000001
  // state[1]: S1     0000000010
  // state[2]: S11    0000000100
  // state[3]: S110   0000001000
  // state[4]: B0     0000010000
  // state[5]: B1     0000100000
  // state[6]: B2     0001000000
  // state[7]: B3     0010000000
  // state[8]: Count  0100000000
  // state[9]: Wait   1000000000

  // Next state logic
  assign S_next =
    // (S and d=0) or (S1 and d=0) or (S110 and d=0) or (Wait and ack=1)
    (state[0] & ~d) |
    (state[1] & ~d) |
    (state[3] & ~d) |
    (state[9] & ack);

  assign S1_next =
    // (S and d=1)
    (state[0] & d);

  assign S11_next =
    // (S1 and d=1) or (S11 and d=1)
    (state[1] & d) |
    (state[2] & d);

  assign S110_next =
    // (S11 and d=0)
    (state[2] & ~d);

  wire B0_next;
  assign B0_next =
    // (S110 and d=1)
    (state[3] & d);

  wire B1_next;
  assign B1_next =
    // (B0 always)
    state[4];

  wire B2_next;
  assign B2_next =
    // (B1 always)
    state[5];

  assign B3_next =
    // (B2 always)
    state[6];

  assign Count_next =
    // (B3 always) or (Count and done_counting==0)
    (state[7]) |
    (state[8] & ~done_counting);

  assign Wait_next =
    // (Count and done_counting==1)
    (state[8] & done_counting);

  // Output logic
  assign shift_ena = state[4] | state[5] | state[6] | state[7];
  assign counting  = state[8];
  assign done      = state[9];

endmodule
