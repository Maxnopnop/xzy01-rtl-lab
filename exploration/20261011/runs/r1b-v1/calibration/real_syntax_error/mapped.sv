module gate(input clk, input rst_n, input data_in, output sequence_detected);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= ; broken  5;
else case(state)
0: state <= data_in ? 1 : 0;
1: state <= data_in ? 1 : 2;
2: state <= data_in ? 1 : 3;
3: state <= data_in ? 4 : 0;
4: state <= data_in ? 1 : 2;
5: state <= data_in ? 6 : 0;
6: state <= data_in ? 7 : 2;
7: state <= data_in ? 8 : 2;
8: state <= data_in ? 9 : 2;
9: state <= data_in ? 10 : 2;
10: state <= data_in ? 1 : 11;
11: state <= data_in ? 1 : 12;
12: state <= data_in ? 13 : 0;
13: state <= data_in ? 14 : 2;
14: state <= data_in ? 1 : 15;
15: state <= data_in ? 1 : 16;
16: state <= data_in ? 17 : 0;
17: state <= data_in ? 1 : 2;
default: state <= 5;
endcase
end
assign sequence_detected = (state==4) || (state==13);
endmodule
