module TopModule (
  input  clk,
  input  areset,
  input  bump_left,
  input  bump_right,
  output walk_left,
  output walk_right
);

  // State encoding
  localparam LEFT  = 1'b0;
  localparam RIGHT = 1'b1;

  reg state, next_state;

  // State register with asynchronous positive-edge reset to LEFT
  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state <= LEFT;
    else
      state <= next_state;
  end

  // Next-state logic
  always_comb begin
    next_state = state;
    case (state)
      LEFT: begin
        if (bump_left || bump_right)
          next_state = RIGHT;
      end
      RIGHT: begin
        if (bump_left || bump_right)
          next_state = LEFT;
      end
      default: next_state = LEFT;
    endcase
  end

  // Output logic (Moore)
  assign walk_left  = (state == LEFT);
  assign walk_right = (state == RIGHT);

endmodule
