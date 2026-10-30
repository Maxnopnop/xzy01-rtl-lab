module escape_frame(input clk,rst_n,feed,input [1:0] symbol,input flush,output reg active,escaped,output reg [1:0] work_sum,work_count,last_sum,last_count,output reg completed);
always @(posedge clk or negedge rst_n) begin
if(!rst_n) begin active<=0;escaped<=0;work_sum<=0;work_count<=0;last_sum<=0;last_count<=0;completed<=0;end
else begin completed<=0;
if(flush)begin active<=0;escaped<=0;work_sum<=0;work_count<=0;end
else if(feed)begin
if(!active)begin if(symbol==0)begin active<=1;escaped<=0;work_sum<=0;work_count<=0;end end
else if(escaped)begin work_sum<=work_sum^symbol;work_count<=work_count+1'b1;escaped<=0;end
else case(symbol)
0:begin work_sum<=0;work_count<=0;end
1:begin last_sum<=work_sum;last_count<=work_count;completed<=1;active<=0;escaped<=0;work_sum<=0;work_count<=0;end
2:escaped<=1;
3:begin work_sum<=work_sum^2'd3;work_count<=work_count+1'b1;end
endcase end end end
endmodule
