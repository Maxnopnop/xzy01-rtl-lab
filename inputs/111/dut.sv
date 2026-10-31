module TopModule (
  input  clk,
  input  areset,
  input  bump_left,
  input  bump_right,
  output walk_left,
  output walk_right
);

  typedef enum logic {
    WALK_LEFT  = 1'b0,
    WALK_RIGHT = 1'b1
  } state_e;

  state_e state_q, state_d;

  // Combinational next-state logic
  always_comb begin
    state_d = state_q;
    case (state_q)
      WALK_LEFT: begin
        if (bump_left || bump_right) state_d = WALK_RIGHT;
      end
      WALK_RIGHT: begin
        if (bump_left || bump_right) state_d = WALK_LEFT;
      end
      default: state_d = WALK_LEFT;
    endcase
  end

  // State register with asynchronous positive-edge reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= WALK_LEFT;
    end else begin
      state_q <= state_d;
    end
  end

  assign walk_left  = (state_q == WALK_LEFT);
  assign walk_right = (state_q == WALK_RIGHT);

endmodule
