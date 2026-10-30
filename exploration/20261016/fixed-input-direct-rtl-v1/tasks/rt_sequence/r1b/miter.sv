
module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));sequence_detector A(.clk(clk),.rst_n(rst_n),.data_in(din),.sequence_detected(a));assign mismatch=g^a;endmodule
