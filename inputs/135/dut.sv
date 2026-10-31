module TopModule (
  input  wire in1,
  input  wire in2,
  input  wire in3,
  output wire out
);

  wire xnor_result;

  // XNOR gate: in1 XNOR in2
  assign xnor_result = ~(in1 ^ in2);

  // XOR gate: xnor_result XOR in3
  assign out = xnor_result ^ in3;

endmodule
