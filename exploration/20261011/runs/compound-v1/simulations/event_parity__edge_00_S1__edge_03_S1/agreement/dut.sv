module event_parity(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 0;
else case(state)
0: state <= din ? 1 : 1;
1: state <= din ? 1 : 1;
default: state <= 0;
endcase
end
assign q = (state==1);
endmodule
