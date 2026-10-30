module dff8(input wire clk, rst, en, input wire [7:0] d, output reg [7:0] q);
always @(posedge clk or posedge rst) if(rst) q<=0; else if(en) q<=d;
endmodule
