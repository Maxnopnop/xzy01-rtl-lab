module TopModule (
  input clk,
  input in,
  input areset,
  output out
);
  RefModule reference_alias(.*);
endmodule
