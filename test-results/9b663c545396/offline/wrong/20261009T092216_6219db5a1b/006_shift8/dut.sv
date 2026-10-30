module shift8(input wire [7:0] a, input wire [2:0] amount, input wire right, output wire [7:0] y);
assign y=a<<amount;
endmodule
