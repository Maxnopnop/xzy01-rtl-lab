module TopModule (
  input  clk,
  input  areset,
  input  x,
  output z
);

  // Moore machine states:
  // S0: no '1' seen yet (input still in its unchanged prefix)
  // S1: first '1' has been seen (output starts complementing)
  typedef enum logic {
    S0 = 1'b0,
    S1 = 1'b1
  } state_e;

  state_e state_q, state_d;

  // Next-state logic
  always_comb begin
    state_d = state_q;
    case (state_q)
      S0: if (x) state_d = S1;
      S1: state_d = S1;
      default: state_d = S0;
    endcase
  end

  // State register with asynchronous positive reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state_q <= S0;
    else
      state_q <= state_d;
  end

  // Moore output:
  // In S0 output equals input; in S1 output is the complement of input.
  assign z = (state_q == S1) ? ~x : x;

endmodule
