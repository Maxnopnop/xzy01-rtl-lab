module edge_detector(input wire clk, rst, din, output reg pulse);
always @(posedge clk) if(rst) pulse<=0; else pulse<=din;
endmodule
