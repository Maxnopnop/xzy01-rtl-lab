module sticky_alarm(input clk, input rst_n, input din, output q);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 3;
else case(state)
0: state <= din ? 1 : 0;
1: state <= din ? 2 : 0;
2: state <= din ? 2 : 2;
3: state <= din ? 1 : 4;
4: state <= din ? 1 : 5;
5: state <= din ? 1 : 0;
default: state <= 3;
endcase
end
assign q = (state==2) || (state==5);
endmodule
