module TopModule (
  input  clk,
  input  x,
  output z
);

  logic xor_q;
  logic and_q;
  logic or_q;

  always_ff @(posedge clk) begin
    xor_q <= x ^ xor_q;
    and_q <= x & ~and_q;
    or_q  <= x | ~or_q;
  end

  assign z = ~(xor_q | and_q | or_q);

endmodule
