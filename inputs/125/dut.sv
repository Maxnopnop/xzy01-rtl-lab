module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  typedef enum logic [1:0] {
    IDLE  = 2'b00,
    INVERT = 2'b01,
    PASS  = 2'b10
  } state_e;

  state_e current_state, next_state;
  logic carry;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= IDLE;
      carry <= 1'b0;
    end else begin
      current_state <= next_state;
      if (current_state == INVERT) begin
        carry <= carry & x;  // Update carry for the next bit processing
      end
    end
  end

  always_comb begin
    case (current_state)
      IDLE: begin
        next_state = INVERT;
        z = x ^ 1'b0; // Initial inversion for the first bit
      end

      INVERT: begin
        next_state = (x ^ carry) ? PASS : INVERT;  // State transition based on current bit and carry
        z = x ^ carry;  // XOR operation to generate 2's complement
      end

      PASS: begin
        next_state = PASS;  // Remain in PASS once determined
        z = x;  // Pass the input as output
      end

      default: begin
        next_state = IDLE;
        z = 1'b0;
      end
    endcase
  end
endmodule
