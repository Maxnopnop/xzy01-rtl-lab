module TopModule (
  input  logic in,
  output logic out
);

  // Implementing the NOT gate by inverting the input signal
  assign out = ~in;

endmodule
