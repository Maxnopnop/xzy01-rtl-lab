module TopModule (
  input  clk,
  input  areset,
  input  x,
  output z
);

  // State encoding for a Moore-type 2's complementer
  typedef enum logic [1:0] {
    S0 = 2'b00,  // no 1 seen yet, output 0
    S1 = 2'b01   // a 1 has been seen, output toggled
  } state_t;

  state_t state, next_state;

  // State register with async positive-edge reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset)
      state <= S0;
    else
      state <= next_state;
  end

  // Next-state and output logic
  always_comb begin
    next_state = state;
    case (state)
      S0: begin
        // Passing through least-significant zeros: output stays 0
        if (x) next_state = S1;
        else   next_state = S0;
      end
      S1: begin
        // After the first 1, invert every incoming bit
        next_state = S1;
      end
      default: next_state = S0;
    endcase
  end

  // Moore output depends only on state
  assign z = (state == S1) ? ~x : 1'b0;

endmodule
