module gold(input clk, input rst_n, input din, output q);
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

module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 3;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 0;
2: state <= din ? 2 : 2;
3: state <= din ? 1 : 4;
4: state <= din ? 1 : 5;
5: state <= din ? 6 : 0;
6: state <= din ? 2 : 7;
7: state <= din ? 1 : 8;
8: state <= din ? 1 : 9;
9: state <= din ? 1 : 10;
10: state <= din ? 1 : 11;
11: state <= din ? 1 : 12;
12: state <= din ? 13 : 0;
13: state <= din ? 14 : 0;
14: state <= din ? 15 : 2;
15: state <= din ? 2 : 2;
default: state <= 3;
endcase
end
assign q = (state==2) || (state==14);
endmodule

module miter(input clk,input rst_n,input din,output mismatch); wire g,a; gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g)); gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a)); assign mismatch=g^a; endmodule
