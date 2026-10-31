module TopModule (
  input  logic clk,
  input  logic x,
  output logic z
);

  logic xor_d, xor_q;
  logic and_d, and_q;
  logic or_d,  or_q;

  // XOR gate: x ^ xor_q
  assign xor_d = x ^ xor_q;

  // AND gate: x & ~and_q
  assign and_d = x & ~and_q;

  // OR gate: x | ~or_q
  assign or_d = x | ~or_q;

  // D flip-flops
  always_ff @(posedge clk) begin
    xor_q <= xor_d;
    and_q <= and_d;
    or_q  <= or_d;
  end

  // Three-input NOR gate
  assign z = ~(xor_q | and_q | or_q);

endmodule
