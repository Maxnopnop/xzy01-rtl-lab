module sequence_detector(input clk, input rst_n, input data_in, output sequence_detected);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 5;
else case(state)
0: state <= data_in ? 1 : 0;
1: state <= data_in ? 1 : 2;
2: state <= data_in ? 1 : 3;
3: state <= data_in ? 4 : 0;
4: state <= data_in ? 1 : 2;
5: state <= data_in ? 1 : 6;
6: state <= data_in ? 7 : 0;
7: state <= data_in ? 1 : 8;
8: state <= data_in ? 1 : 3;
default: state <= 5;
endcase
end
assign sequence_detected = (state==4) || (state==8);
endmodule
