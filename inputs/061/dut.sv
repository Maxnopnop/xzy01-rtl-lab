module TopModule (
  input  clk,
  input  areset,
  input  in,
  output out
);

  // State encoding: A = 0, B = 1
  reg state;

  always @(posedge clk or posedge areset) begin
    if (areset)
      state <= 1'b1; // B
    else begin
      case (state)
        1'b0: state <= in ? 1'b0 : 1'b1; // A --1--> A, A --0--> B
        1'b1: state <= in ? 1'b1 : 1'b0; // B --1--> B, B --0--> A
      endcase
    end
  end

  assign out = state;

endmodule
