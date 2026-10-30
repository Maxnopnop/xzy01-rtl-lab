module gold(input clk,input rst_n,input din,output q);
reg [1:0] phase; always @(posedge clk or negedge rst_n) if(!rst_n) phase<=0; else if(phase==0) begin if(din) phase<=1;end else if(phase==1) phase<=2; else if(phase==2) phase<=3; else if(!din) phase<=0; assign q=phase==2;
endmodule
