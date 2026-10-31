module TopModule (
  input  clk,
  input  areset,
  input  bump_left,
  input  bump_right,
  output logic walk_left,
  output logic walk_right
);

  typedef enum logic {WalkLeft, WalkRight} state_t;
  state_t state, next_state;

  always_comb begin
    next_state = state;

    case (state)
      WalkLeft: begin
        if (bump_left || bump_right)
          next_state = WalkRight;
      end

      WalkRight: begin
        if (bump_left || bump_right)
          next_state = WalkLeft;
      end

      default: begin
        next_state = WalkLeft;
      end
    endcase
  end

  always_comb begin
    walk_left = (state == WalkLeft);
    walk_right = (state == WalkRight);
  end

  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state <= WalkLeft;
    else
      state <= next_state;
  end

endmodule
