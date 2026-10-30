module gate(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 0;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 2;
2: state <= din ? 3 : 3;
3: state <= din ? 3 : 0;
default: state <= 0;
endcase
end
assign q = (state==2);
endmodule
