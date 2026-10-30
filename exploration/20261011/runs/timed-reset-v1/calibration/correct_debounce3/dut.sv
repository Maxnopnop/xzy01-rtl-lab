module debounce3(input clk,input rst_n,input din,output q);
reg high;reg [1:0] streak; always @(posedge clk or negedge rst_n) if(!rst_n) begin high<=0;streak<=0;end else if(din==high) streak<=0;else if((!high && streak==2)||(high && streak==1)) begin high<=!high;streak<=0;end else streak<=streak+1; assign q=high;
endmodule
