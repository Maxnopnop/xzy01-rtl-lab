module gold(input clk, input rst_n, input din, output q);
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

module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 2;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 0 : 1;
2: state <= din ? 1 : 3;
3: state <= din ? 1 : 4;
4: state <= din ? 5 : 0;
5: state <= din ? 6 : 1;
6: state <= din ? 7 : 0;
7: state <= din ? 0 : 8;
8: state <= din ? 9 : 1;
9: state <= din ? 1 : 10;
10: state <= din ? 11 : 0;
11: state <= din ? 0 : 12;
12: state <= din ? 0 : 13;
13: state <= din ? 14 : 1;
14: state <= din ? 1 : 0;
default: state <= 2;
endcase
end
assign q = (state==1) || (state==5) || (state==7) || (state==8) || (state==11) || (state==12) || (state==13) || (state==14);
endmodule

module miter(input clk,input rst_n,input din,output mismatch); wire g,a; gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g)); gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a)); assign mismatch=g^a; endmodule
