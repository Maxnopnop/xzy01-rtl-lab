module TopModule (
  input  logic [7:0] a,
  input  logic [7:0] b,
  output logic [7:0] s,
  output logic       overflow
);

  logic [7:0] sum;
  logic       ovf;

  // Perform 2's complement addition
  assign sum = a + b;
  assign s   = sum;

  // Overflow detection for signed addition:
  // When the sign of a and b is the same but different from the sign of sum.
  assign ovf = (~a[7] & ~b[7] &  sum[7]) | // positive + positive = negative (overflow)
               ( a[7] &  b[7] & ~sum[7]);  // negative + negative = positive (overflow)

  assign overflow = ovf;

endmodule
