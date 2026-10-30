module gold(input clk, input rst_n, input din, output q);
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

module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 5;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 0;
2: state <= din ? 3 : 0;
3: state <= din ? 3 : 4;
4: state <= din ? 3 : 0;
5: state <= din ? 1 : 6;
6: state <= din ? 1 : 7;
7: state <= din ? 1 : 8;
8: state <= din ? 9 : 0;
9: state <= din ? 2 : 10;
10: state <= din ? 11 : 0;
11: state <= din ? 12 : 0;
12: state <= din ? 13 : 0;
13: state <= din ? 14 : 4;
14: state <= din ? 15 : 4;
15: state <= din ? 3 : 16;
16: state <= din ? 17 : 0;
17: state <= din ? 3 : 4;
default: state <= 5;
endcase
end
assign q = (state==3) || (state==4) || (state==13) || (state==14) || (state==15) || (state==16);
endmodule

module miter(input clk,input rst_n,input din,output mismatch); wire g,a; gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g)); gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a)); assign mismatch=g^a; endmodule
