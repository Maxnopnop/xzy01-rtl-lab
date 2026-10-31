module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic in,
  output logic out
);

  typedef enum logic [0:0] {
    A = 1'b0,
    B = 1'b1
  } state_e;

  state_e state_q, state_d;

  // State register with asynchronous active-high reset to B
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= B;
    end else begin
      state_q <= state_d;
    end
  end

  // Next state logic
  always_comb begin
    unique case (state_q)
      B: begin
        if (in)
          state_d = B;
        else
          state_d = A;
      end
      A: begin
        if (in)
          state_d = A;
        else
          state_d = B;
      end
      default: state_d = B;
    endcase
  end

  // Moore output logic
  assign out = (state_q == B);

endmodule
