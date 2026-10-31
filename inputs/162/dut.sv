module TopModule(
  input  logic [7:0] a,
  input  logic [7:0] b,
  output logic [7:0] s,
  output logic overflow
);

  logic [8:0] sum;

  // Perform the addition with an extra bit to detect overflow
  assign sum = {a[7], a} + {b[7], b};

  // Assign sum to output s, truncating the overflow bit
  assign s = sum[7:0];

  // Detect signed overflow
  // Overflow occurs if the sign of sum[8] is different from s[7]
  assign overflow = (sum[8] != s[7]);

endmodule
