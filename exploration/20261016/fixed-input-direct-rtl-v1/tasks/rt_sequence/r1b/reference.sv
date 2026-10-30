module gold(input clk,input rst_n,input din,output q);
reg [3:0] history; always @(posedge clk or negedge rst_n) if(!rst_n) history<=0; else history<={history[2:0],din}; assign q=history==4'b1001;
endmodule
