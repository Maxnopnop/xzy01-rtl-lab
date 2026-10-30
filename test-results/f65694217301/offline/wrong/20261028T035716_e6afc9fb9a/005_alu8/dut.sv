module alu8(input wire [7:0] a, b, input wire [2:0] op, output reg [7:0] y);
always @* y=a+b;
endmodule
