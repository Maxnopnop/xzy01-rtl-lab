module TopModule (
  input        clk,
  input        reset,
  input  [2:0] s,
  output       fr2,
  output       fr1,
  output       fr0,
  output       dfr
);

  typedef enum logic [1:0] {
    StBelowS0,
    StBetweenS0S1,
    StBetweenS1S2,
    StAboveS2
  } state_e;

  state_e state_d, state_q;

  always_comb begin
    state_d = state_q;
    case (state_q)
      StBelowS0: begin
        if (s[0])       state_d = StBetweenS0S1;
      end
      StBetweenS0S1: begin
        if (s[1])       state_d = StBetweenS1S2;
        else if (!s[0]) state_d = StBelowS0;
      end
      StBetweenS1S2: begin
        if (s[2])       state_d = StAboveS2;
        else if (!s[1]) state_d = StBetweenS0S1;
      end
      StAboveS2: begin
        if (!s[2])      state_d = StBetweenS1S2;
      end
      default: state_d = StBelowS0;
    endcase
  end

  always_ff @(posedge clk) begin
    if (reset) state_q <= StBelowS0;
    else       state_q <= state_d;
  end

  always_comb begin
    case (state_q)
      StBelowS0: begin
        fr0 = 1'b1;
        fr1 = 1'b1;
        fr2 = 1'b1;
        dfr = 1'b1;
      end
      StBetweenS0S1: begin
        fr0 = 1'b1;
        fr1 = 1'b1;
        fr2 = 1'b0;
        dfr = (state_d == StBelowS0);
      end
      StBetweenS1S2: begin
        fr0 = 1'b1;
        fr1 = 1'b0;
        fr2 = 1'b0;
        dfr = (state_d == StBetweenS0S1);
      end
      StAboveS2: begin
        fr0 = 1'b0;
        fr1 = 1'b0;
        fr2 = 1'b0;
        dfr = 1'b0;
      end
      default: begin
        fr0 = 1'b1;
        fr1 = 1'b1;
        fr2 = 1'b1;
        dfr = 1'b1;
      end
    endcase
  end

endmodule
