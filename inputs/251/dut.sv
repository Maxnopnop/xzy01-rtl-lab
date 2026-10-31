module TopModule (
  input  logic clk,
  input  logic x,
  output logic z
);

  // State registers for storing outputs of the flip-flops
  logic xor_ff, and_ff, or_ff;

  // Intermediate wires for gate outputs
  logic xor_out, and_out, or_out;

  // Combinational logic: XOR, AND, OR gates
  assign xor_out = x ^ xor_ff;
  assign and_out = x & ~and_ff;
  assign or_out = x | ~or_ff;

  // Sequential logic: D flip-flops
  always_ff @(posedge clk) begin
    xor_ff <= xor_out;
    and_ff <= and_out;
    or_ff <= or_out;
  end

  // Combinational logic: Three-input NOR gate
  assign z = ~(xor_ff | and_ff | or_ff);

endmodule
