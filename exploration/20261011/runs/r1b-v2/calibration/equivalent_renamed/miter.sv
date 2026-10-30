module gold(input clk,input rst_n,input din,output q);
reg [3:0] history; always @(posedge clk or negedge rst_n) if(!rst_n) history<=0; else history<={history[2:0],din}; assign q=history==4'b1001;
endmodule
module gate(input clk, input rst_n, input data_in, output sequence_detected);
reg [4:0] state;
always @(posedge clk or negedge rst_n) begin
if(rst_n==1'b0) state <= 0;
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

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.data_in(din),.sequence_detected(a));assign mismatch=g^a;endmodule
