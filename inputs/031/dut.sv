module TopModule (
  input  [7:0] a,
  input  [7:0] b,
  output [7:0] s,
  output overflow
);

  wire [7:0] sum;
  wire [7:0] sum_unsigned;

  assign sum = a + b;
  assign s = sum;

  // Signed overflow: operands have same sign and result sign differs
  assign overflow = (a[7] == b[7]) && (sum[7] != a[7]);

endmodule
