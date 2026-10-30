module sequence_detector(input clk, input rst_n, input data_in, output sequence_detected);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if (rst_n == 1'b0) state <= 0;
else case (state)
0: if(data_in) state <= 1; else state <= 0;
1: if(data_in) state <= 1; else state <= 2;
2: if(data_in) state <= 1; else state <= 3;
3: if(data_in) state <= 4; else state <= 0;
4: if(data_in) state <= 1; else state <= 2;
default: state <= 0;
endcase
end
assign sequence_detected = (state == 4);
endmodule
