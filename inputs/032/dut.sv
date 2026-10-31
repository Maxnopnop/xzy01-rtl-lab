module TopModule (
  input  [7:0] a,
  input  [7:0] b,
  output [7:0] s,
  output       overflow
);

  logic [7:0] sum;
  assign sum = a + b;
  assign s = sum;

  // Signed overflow: operands have same sign but result differs
  assign overflow = (a[7] == b[7]) && (sum[7] != a[7]);

endmodule
