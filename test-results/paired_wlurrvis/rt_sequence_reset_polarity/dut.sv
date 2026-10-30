module sequence_detector(input clk, input rst_n, input data_in, output sequence_detected);
reg [4:0] state;
always @(posedge clk or posedge rst_n) begin
if(rst_n==1'b1) state <= 0;
else case(state)
0: state <= data_in ? 1 : 0;
1: state <= data_in ? 1 : 2;
2: state <= data_in ? 1 : 3;
3: state <= data_in ? 4 : 0;
4: state <= data_in ? 1 : 2;
default: state <= 0;
endcase
end
assign sequence_detected = (state==4);
endmodule
