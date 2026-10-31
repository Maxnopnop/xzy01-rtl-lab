module TopModule (
  input  logic [7:0] in,
  output logic [31:0] out
);

  always_comb begin
    // Sign-extend the 8-bit input to 32 bits
    out = {{24{in[7]}}, in};
  end

endmodule
