module sequence101(input wire clk, rst, din, output reg match);
reg [1:0] hist; always @(posedge clk) if(rst) begin hist<=0; match<=0; end else begin match<=(hist==1 && din); hist<={hist[0],din}; end
endmodule
