module TopModule (
  input  clk,
  input  areset,
  input  in,
  output out
);

  typedef enum logic {
    STATE_A = 1'b0,
    STATE_B = 1'b1
  } state_e;

  state_e state, next_state;

  always_comb begin
    next_state = state;
    case (state)
      STATE_A: next_state = in ? STATE_A : STATE_B;
      STATE_B: next_state = in ? STATE_B : STATE_A;
      default: next_state = STATE_B;
    endcase
  end

  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state <= STATE_B;
    else
      state <= next_state;
  end

  assign out = state;

endmodule
