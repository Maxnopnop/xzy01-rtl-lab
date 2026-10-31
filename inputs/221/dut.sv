module TopModule (
  input  d,
  input  done_counting,
  input  ack,
  input [9:0] state,
  output B3_next,
  output S_next,
  output S1_next,
  output Count_next,
  output Wait_next,
  output done,
  output counting,
  output shift_ena
);

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

  logic [9:0] next_state;

  always_comb begin
    next_state = state;

    case (state)
      S: begin
        if (d)
          next_state = S1;
        else
          next_state = S;
      end

      S1: begin
        if (d)
          next_state = S11;
        else
          next_state = S;
      end

      S11: begin
        if (d)
          next_state = S11;
        else
          next_state = S110;
      end

      S110: begin
        if (d)
          next_state = B0;
        else
          next_state = S;
      end

      B0:    next_state = B1;
      B1:    next_state = B2;
      B2:    next_state = B3;
      B3:    next_state = Count;

      Count: begin
        if (done_counting)
          next_state = Wait;
        else
          next_state = Count;
      end

      Wait: begin
        if (ack)
          next_state = S;
        else
          next_state = Wait;
      end

      default: next_state = S;
    endcase
  end

  assign B3_next    = next_state == B3;
  assign S_next     = next_state == S;
  assign S1_next    = next_state == S1;
  assign Count_next = next_state == Count;
  assign Wait_next  = next_state == Wait;

  assign shift_ena = (state == B0) || (state == B1) ||
                     (state == B2) || (state == B3);
  assign counting  = state == Count;
  assign done      = state == Wait;

endmodule
