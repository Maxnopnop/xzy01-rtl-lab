module request_delay(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 3;
else case(state)
0: state <= din ? 0 : 3;
1: state <= din ? 0 : 0;
2: state <= din ? 1 : 1;
3: state <= din ? 2 : 3;
default: state <= 3;
endcase
end
assign q = (state==1);
endmodule
