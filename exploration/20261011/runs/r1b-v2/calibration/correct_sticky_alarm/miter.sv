module gold(input clk,input rst_n,input din,output q);
reg previous,alarm; always @(posedge clk or negedge rst_n) if(!rst_n) begin previous<=0;alarm<=0;end else begin previous<=din;alarm<=alarm|(previous&din);end assign q=alarm;
endmodule
module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 0;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 0;
2: state <= din ? 2 : 2;
default: state <= 0;
endcase
end
assign q = (state==2);
endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
