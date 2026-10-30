module sequence_detector(input clk,input rst_n,input data_in,output sequence_detected);
reg [3:0] history; always @(posedge clk or negedge rst_n) if(!rst_n) history<=0; else history<={history[2:0],data_in}; assign sequence_detected=history==4'b1001;
endmodule
