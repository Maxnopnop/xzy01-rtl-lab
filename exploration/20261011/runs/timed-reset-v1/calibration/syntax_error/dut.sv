module event_parity(input clk,input rst_n,input din,output q);
reg parity; always @(posedge clk or negedge rst_n) if(!rst_n) parity<= ; broken 0; else parity<=parity^din; assign q=parity;
endmodule
