module TopModule (
  input  logic [7:0] a,
  input  logic [7:0] b,
  output logic [7:0] s,
  output logic       overflow
);

  always_comb begin
    // Add the two 8-bit 2's complement numbers
    s = a + b;
    // Compute overflow: overflow occurs if the sign bit changes incorrectly
    overflow = (a[7] == b[7]) && (s[7] != a[7]);
  end

endmodule
