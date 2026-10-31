module TopModule (
  input  logic [7:0] a,
  input  logic [7:0] b,
  output logic [7:0] s,
  output logic       overflow
);

  logic [7:0] sum;
  logic       ovf;

  // Perform signed addition
  assign sum = a + b;
  assign s   = sum;

  // Overflow detection: if sign of a and b are equal and sign of sum differs
  assign ovf = (~a[7] & ~b[7] & sum[7]) // positive + positive = negative
            | ( a[7] &  b[7] & ~sum[7]); // negative + negative = positive
  assign overflow = ovf;

endmodule
