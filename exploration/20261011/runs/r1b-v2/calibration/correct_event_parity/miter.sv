module gold(input clk,input rst_n,input din,output q);
reg parity; always @(posedge clk or negedge rst_n) if(!rst_n) parity<=0; else parity<=parity^din; assign q=parity;
endmodule
module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 0;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 0 : 1;
default: state <= 0;
endcase
end
assign q = (state==1);
endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
