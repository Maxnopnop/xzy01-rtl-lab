module TopModule (
  input  clk,
  input  areset,
  input  x,
  output z
);

  logic seen_one;

  assign z = seen_one ? ~x : x;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      seen_one <= 1'b0;
    end else if (!seen_one && x) begin
      seen_one <= 1'b1;
    end
  end

endmodule
