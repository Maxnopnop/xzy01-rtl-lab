module TopModule (
  input  a,
  input  b,
  input  c,
  input  d,
  input  e,
  output out
);

  assign out = ~a ^ a;

endmodule
