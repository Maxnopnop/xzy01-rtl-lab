module TopModule (
  input  d,
  input  done_counting,
  input  ack,
  input  [9:0] state,
  output B3_next,
  output S_next,
  output S1_next,
  output Count_next,
  output Wait_next,
  output done,
  output counting,
  output shift_ena
);

  // One-hot state encoding
  wire S_w    = state[0];
  wire S1_w   = state[1];
  wire S11_w  = state[2];
  wire S110_w = state[3];
  wire B0_w   = state[4];
  wire B1_w   = state[5];
  wire B2_w   = state[6];
  wire B3_w   = state[7];
  wire Count_w= state[8];
  wire Wait_w = state[9];

  // Next-state logic
  assign S_next    = (S_w  && ~d) |
                     (S1_w && ~d) |
                     (S110_w && ~d) |
                     (Wait_w && ack);

  assign S1_next   = (S_w  && d);

  assign B3_next   = B2_w;

  assign Count_next= B3_w;

  assign Wait_next = (Count_w && done_counting);

  // Output logic
  assign shift_ena = B0_w | B1_w | B2_w | B3_w;

  assign counting  = Count_w;

  assign done      = Wait_w;

endmodule
