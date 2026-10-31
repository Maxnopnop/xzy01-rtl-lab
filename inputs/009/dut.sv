module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  logic seen_one;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      seen_one <= 1'b0;
    end else begin
      if (x) begin
        seen_one <= 1'b1;
      end
    end
  end

  assign z = x ^ seen_one;

endmodule
