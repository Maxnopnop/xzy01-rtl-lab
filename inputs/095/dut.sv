module TopModule (
  input  clk,
  input  x,
  output z
);

  logic xor_ff_q;
  logic and_ff_q;
  logic or_ff_q;

  logic xor_gate_out;
  logic and_gate_out;
  logic or_gate_out;

  assign xor_gate_out = x ^ xor_ff_q;
  assign and_gate_out = x & ~and_ff_q;
  assign or_gate_out  = x | ~or_ff_q;

  always_ff @(posedge clk) begin
    xor_ff_q <= xor_gate_out;
    and_ff_q <= and_gate_out;
    or_ff_q  <= or_gate_out;
  end

  assign z = ~(xor_ff_q | and_ff_q | or_ff_q);

endmodule
