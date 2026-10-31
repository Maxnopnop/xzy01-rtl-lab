module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic bump_left,
  input  logic bump_right,
  output logic walk_left,
  output logic walk_right
);

  typedef enum logic [0:0] {
    WalkLeft,   // Lemming walking left, changes direction if bump_left or bump_right
    WalkRight   // Lemming walking right, changes direction if bump_left or bump_right
  } state_e;

  state_e state_q, state_d;

  // Combinational block: Output decode and next state logic
  always_comb begin
    // Default assignments
    state_d   = state_q;
    walk_left = 1'b0;
    walk_right = 1'b0;

    case (state_q)
      // Lemming is walking left
      WalkLeft: begin
        walk_left = 1'b1;
        // If bump on left or right or both: switch to WalkRight
        if (bump_left || bump_right)
          state_d = WalkRight;
      end
      // Lemming is walking right
      WalkRight: begin
        walk_right = 1'b1;
        // If bump on left or right or both: switch to WalkLeft
        if (bump_left || bump_right)
          state_d = WalkLeft;
      end
      default: begin
        state_d = WalkLeft;
      end
    endcase
  end

  // State register: asynchronous reset, active high
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= WalkLeft;
    end else begin
      state_q <= state_d;
    end
  end

endmodule
