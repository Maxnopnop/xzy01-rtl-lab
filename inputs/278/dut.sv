module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic bump_left,
  input  logic bump_right,
  output logic walk_left,
  output logic walk_right
);

  typedef enum logic [1:0] {
    WalkLeft,   // State where the Lemming walks left
    WalkRight   // State where the Lemming walks right
  } state_t;

  state_t current_state, next_state;

  // Combinational logic to determine next state and outputs
  always_comb begin
    // Default assignments
    next_state  = current_state;
    walk_left   = 0;
    walk_right  = 0;
    
    case (current_state)
      WalkLeft: begin
        // Lemming currently walking left
        walk_left = 1;
        if (bump_left || (bump_left && bump_right)) begin
          next_state = WalkRight;
        end
      end

      WalkRight: begin
        // Lemming currently walking right
        walk_right = 1;
        if (bump_right || (bump_left && bump_right)) begin
          next_state = WalkLeft;
        end
      end
    endcase
  end

  // Sequential logic to update current state
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= WalkLeft; // Reset state is WalkLeft
    end else begin
      current_state <= next_state;
    end
  end

endmodule
