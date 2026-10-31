module TopModule (
  input      clk,
  input      areset,
  input      bump_left,
  input      bump_right,
  output     walk_left,
  output     walk_right
);

  typedef enum logic {
    StWalkLeft,
    StWalkRight
  } state_e;

  state_e state_d, state_q;

  always_comb begin
    state_d = state_q;

    case (state_q)
      StWalkLeft: begin
        if (bump_left || bump_right)
          state_d = StWalkRight;
      end
      StWalkRight: begin
        if (bump_left || bump_right)
          state_d = StWalkLeft;
      end
      default: state_d = StWalkLeft;
    endcase
  end

  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state_q <= StWalkLeft;
    else
      state_q <= state_d;
  end

  assign walk_left  = (state_q == StWalkLeft);
  assign walk_right = (state_q == StWalkRight);

endmodule
