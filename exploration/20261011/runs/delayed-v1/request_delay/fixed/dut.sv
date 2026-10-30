module request_delay(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 4;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 2;
2: state <= din ? 3 : 3;
3: state <= din ? 3 : 0;
4: state <= din ? 1 : 5;
5: state <= din ? 6 : 0;
6: state <= din ? 7 : 2;
7: state <= din ? 8 : 3;
8: state <= din ? 9 : 0;
9: state <= din ? 10 : 0;
10: state <= din ? 11 : 0;
11: state <= din ? 12 : 0;
12: state <= din ? 3 : 13;
13: state <= din ? 1 : 14;
14: state <= din ? 1 : 15;
15: state <= din ? 1 : 16;
16: state <= din ? 1 : 0;
default: state <= 4;
endcase
end
assign q = (state==2) || (state==7) || (state==16);
endmodule
