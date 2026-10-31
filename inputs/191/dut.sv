module TopModule (
  input  logic [4:0] a,
  input  logic [4:0] b,
  input  logic [4:0] c,
  input  logic [4:0] d,
  input  logic [4:0] e,
  input  logic [4:0] f,
  output logic [7:0] w,
  output logic [7:0] x,
  output logic [7:0] y,
  output logic [7:0] z
);
  logic [31:0] concat_in;
  assign concat_in = {a, b, c, d, e, f, 2'b11};
  assign w = concat_in[31:24];
  assign x = concat_in[23:16];
  assign y = concat_in[15:8];
  assign z = concat_in[7:0];
endmodule
