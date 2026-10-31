module TopModule (
  input  [7:0] in,
  output [2:0] pos
);

  logic [2:0] pos_d;

  always_comb begin
    casez (in)
      8'b???????1: pos_d = 3'd0;
      8'b??????10: pos_d = 3'd1;
      8'b?????100: pos_d = 3'd2;
      8'b????1000: pos_d = 3'd3;
      8'b???10000: pos_d = 3'd4;
      8'b??100000: pos_d = 3'd5;
      8'b?1000000: pos_d = 3'd6;
      8'b10000000: pos_d = 3'd7;
      default:      pos_d = 3'd0;
    endcase
  end

  assign pos = pos_d;

endmodule
