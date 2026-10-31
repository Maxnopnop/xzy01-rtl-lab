module TopModule (
  input  clk,
  input  areset,
  input  in,
  output out
);

  typedef enum logic {
    A = 1'b0,
    B = 1'b1
  } state_e;

  state_e state_q, state_d;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= B;
    end else begin
      state_q <= state_d;
    end
  end

  always_comb begin
    case (state_q)
      A: state_d = in ? A : B;
      B: state_d = in ? B : A;
      default: state_d = B;
    endcase
  end

  assign out = (state_q == B);

endmodule
