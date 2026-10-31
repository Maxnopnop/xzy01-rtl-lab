module TopModule (
  input  logic clk,
  input  logic x,
  output logic z
);

  // Registers for D flip-flops (reset to zero on power-up)
  logic ff_xor_q, ff_and_q, ff_or_q;
  logic ff_xor_d, ff_and_d, ff_or_d;

  // Combinational logic for flip-flop inputs
  always_comb begin
    ff_xor_d = x ^ ff_xor_q;
    ff_and_d = x & ~ff_and_q;
    ff_or_d  = x | ~ff_or_q;
  end

  // State registers (D flip-flops)
  always_ff @(posedge clk) begin
    ff_xor_q <= ff_xor_d;
    ff_and_q <= ff_and_d;
    ff_or_q  <= ff_or_d;
  end

  // Output: NOR of the three flip-flop outputs
  assign z = ~(ff_xor_q | ff_and_q | ff_or_q);

endmodule
