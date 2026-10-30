module edge_detector(input wire clk, rst, din, output reg pulse);
reg prev; always @(posedge clk) if(rst) begin prev<=0; pulse<=0; end else begin pulse<=din & ~prev; prev<=din; end
endmodule
