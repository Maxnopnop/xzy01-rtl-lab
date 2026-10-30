module updown8(input wire clk, rst, en, up, output reg [7:0] q);
always @(posedge clk) if(rst) q<=0; else if(en) q<=q+1;
endmodule
