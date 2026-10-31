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

  // One-hot state encoding:
  // (S, S1, S11, S110, B0, B1, B2, B3, Count, Wait)
  // = (bit0, bit1, bit2, bit3, bit4, bit5, bit6, bit7, bit8, bit9)
  localparam logic [9:0] S     = 10'b0000000001;
  localparam logic [9:0] S1    = 10'b0000000010;
  localparam logic [9:0] S11   = 10'b0000000100;
  localparam logic [9:0] S110  = 10'b0000001000;
  localparam logic [9:0] B0    = 10'b0000010000;
  localparam logic [9:0] B1    = 10'b0000100000;
  localparam logic [9:0] B2    = 10'b0001000000;
  localparam logic [9:0] B3    = 10'b0010000000;
  localparam logic [9:0] Count = 10'b0100000000;
  localparam logic [9:0] Wait  = 10'b1000000000;

  // Next-state logic (by inspection of one-hot transitions)
  assign B3_next    = (state == B2);
  assign S_next     = ((state == S)    && !d) ||
                      ((state == S1)   && !d) ||
                      ((state == S110) && !d) ||
                      ((state == Wait) &&  ack);
  assign S1_next    = (state == S) && d;
  assign Count_next = (state == B3);
  assign Wait_next  = (state == Count) && done_counting;

  // Output logic (Moore outputs)
  assign shift_ena = (state == B0) || (state == B1) || (state == B2) || (state == B3);
  assign counting  = (state == Count);
  assign done      = (state == Wait);

endmodule
