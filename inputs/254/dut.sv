module TopModule (
  input        clk,
  input        x,
  output logic z
);

  // State (outputs of the three D flip-flops)
  logic ff_xor_q, ff_and_q, ff_or_q;

  // Combinational logic for D inputs of flip-flops
  logic ff_xor_d, ff_and_d, ff_or_d;

  // D inputs for the three flip-flops
  always_comb begin
    ff_xor_d = x ^ ff_xor_q;
    ff_and_d = x & ~ff_and_q;
    ff_or_d  = x | ~ff_or_q;
  end

  // Clocked, synchronous state register
  always_ff @(posedge clk) begin
    ff_xor_q <= ff_xor_d;
    ff_and_q <= ff_and_d;
    ff_or_q  <= ff_or_d;
  end

  // Output logic: NOR of the flip-flop outputs
  always_comb begin
    z = ~(ff_xor_q | ff_and_q | ff_or_q);
  end

  // Optional: Initial values for simulation friendliness (will reset to zero before use in hardware)
  initial begin
    ff_xor_q = 1'b0;
    ff_and_q = 1'b0;
    ff_or_q  = 1'b0;
  end

endmodule
