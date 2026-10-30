module retrigger_window(input clk,rst_n,trigger,tick,enable,input [1:0] length,output reg active,output reg [1:0] remaining,output reg expired);
always @(posedge clk or negedge rst_n) begin
 if(!rst_n) begin active<=0;remaining<=0;expired<=0;end
 else begin
  expired<=0;
  if(trigger && !(active && enable && tick)) begin active<=1;remaining<=(length==0)?2'd1:length;end
  else if(active && enable && tick) begin
   if(remaining==1) begin active<=0;remaining<=0;expired<=1;end
   else remaining<=remaining-1'b1;
  end
 end
end
endmodule
