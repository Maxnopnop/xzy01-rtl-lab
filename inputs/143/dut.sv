module TopModule (
  input  logic [99:0] in,
  output logic [99:0] out
);

  // Reverse the ordering of the bits in the input and assign to output
  always_comb begin
    for (int i = 0; i < 100; i++) begin
      out[i] = in[99-i];
    end
  end
  
endmodule
