module gold(input clk,input rst_n,input din,output q);
reg high;reg [1:0] streak; always @(posedge clk or negedge rst_n) if(!rst_n) begin high<=0;streak<=0;end else if(din==high) streak<=0;else if((!high && streak==2)||(high && streak==1)) begin high<=!high;streak<=0;end else streak<=streak+1; assign q=high;
endmodule
module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 0;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 0;
2: state <= din ? 3 : 0;
3: state <= din ? 3 : 4;
4: state <= din ? 3 : 0;
default: state <= 0;
endcase
end
assign q = (state==3) || (state==4);
endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
