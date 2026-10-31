module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic in,
  output logic out
);

  typedef enum logic [0:0] {
    B = 1'b0,  // State B
    A = 1'b1   // State A
  } state_e;

  state_e current_state, next_state;

  // Asynchronous reset and state register
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= B;
    end else begin
      current_state <= next_state;
    end
  end

  // Combinational logic for next state and output
  always_comb begin
    // Default assignments
    next_state = current_state;
    out = (current_state == B) ? 1'b1 : 1'b0; 

    case (current_state)
      B: begin
        // State B: Output is 1, transitions
        if (in) next_state = B;
        else next_state = A;
      end
      A: begin
        // State A: Output is 0, transitions
        if (in) next_state = A;
        else next_state = B;
      end
    endcase
  end

endmodule
