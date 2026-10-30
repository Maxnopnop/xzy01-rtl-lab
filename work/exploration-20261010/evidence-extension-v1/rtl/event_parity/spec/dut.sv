module event_parity(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 2;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 0 : 1;
2: state <= din ? 1 : 3;
3: state <= din ? 4 : 0;
4: state <= din ? 0 : 1;
default: state <= 2;
endcase
end
assign q = (state==1);
endmodule
