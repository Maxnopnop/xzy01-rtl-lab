module sequence101(input wire clk, rst, din, output reg match);
reg [1:0] hist; reg [1:0] count; always @(posedge clk) if(rst) begin hist<=0; count<=0; match<=0; end else begin match<=(count>=2 && hist==2 && din); hist<={hist[0],din}; if(count<2) count<=count+1; end
endmodule
