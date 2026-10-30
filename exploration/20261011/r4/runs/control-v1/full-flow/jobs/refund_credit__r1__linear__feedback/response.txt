module refund_credit(input clk,rst_n,submit,input [1:0] refund,cost,output reg [2:0] credit,output reg accepted,rejected,output can_pay);
wire [3:0] sum={1'b0,credit}+{2'b0,refund};wire [3:0] funded=sum>5?5:sum;
assign can_pay=rst_n&&(cost!=0)&&(funded>=cost);
always @(posedge clk or negedge rst_n) begin
if(!rst_n) begin credit<= ;;accepted<=0;rejected<=0;end
else begin accepted<=0;rejected<=0;credit<=funded;
if(submit) begin if(cost!=0 && funded>=cost) begin credit<=funded-cost;accepted<=1;end else rejected<=1;end
end end
endmodule
