module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

  typedef enum logic [0:0] {
    STATE_A = 1'b0, // State A
    STATE_B = 1'b1  // State B
  } state_e;

  state_e state_q, state_d;

  // State transition logic
  always_comb begin
    case (state_q)
      STATE_A: state_d = (in) ? STATE_A : STATE_B;
      STATE_B: state_d = (in) ? STATE_B : STATE_A;
      default: state_d = STATE_B; // default state is STATE_B
    endcase
  end

  // State register with asynchronous reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= STATE_B; // Asynchronously reset to state B
    end else begin
      state_q <= state_d;
    end
  end

  // Output logic
  assign out = (state_q == STATE_B);

endmodule
