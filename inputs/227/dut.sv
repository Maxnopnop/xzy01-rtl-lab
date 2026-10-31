module TopModule (
  input        [2:0] a,
  input        [2:0] b,
  output logic [2:0] out_or_bitwise,
  output logic       out_or_logical,
  output logic [5:0] out_not
);

  // Bitwise OR of a and b, 3 bits
  assign out_or_bitwise = a | b;

  // Logical OR: true if any bit in a or b is '1'
  assign out_or_logical = |a | |b;

  // out_not: [5:3]=~b, [2:0]=~a
  assign out_not = {~b, ~a};

endmodule
