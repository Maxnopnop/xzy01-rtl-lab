module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic bump_left,
  input  logic bump_right,
  output logic walk_left,
  output logic walk_right
);

  // State enumeration: WalkingLeft - Lemming is walking left,
  //                   WalkingRight - Lemming is walking right
  typedef enum logic [0:0] {
    WalkingLeft,
    WalkingRight
  } state_e;

  state_e state_q, state_d;

  // Combinational logic: next state and outputs
  always_comb begin
    // Default assignments
    state_d = state_q;
    walk_left = 1'b0;
    walk_right = 1'b0;

    case (state_q)
      // Walking left state: lemming is currently walking left
      WalkingLeft: begin
        walk_left = 1'b1;
        // If bumped on the left (or both), switch to walking right
        if (bump_left || bump_right) begin
          state_d = WalkingRight;
        end
      end

      // Walking right state: lemming is currently walking right
      WalkingRight: begin
        walk_right = 1'b1;
        // If bumped on the right (or both), switch to walking left
        if (bump_left || bump_right) begin
          state_d = WalkingLeft;
        end
      end

      // No default; all states covered
    endcase
  end

  // Sequential logic: state update with asynchronous reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= WalkingLeft;
    end else begin
      state_q <= state_d;
    end
  end

endmodule
