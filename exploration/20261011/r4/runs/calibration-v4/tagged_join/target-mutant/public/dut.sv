module tagged_join(input clk,rst_n,av,atag,input [1:0] adata,input bv,btag,input [1:0] bdata,input flush,output reg pending_a,pending_b,joined,output reg [1:0] result);
reg ta,tag_b;reg [1:0] da,db;reg va1,vb1,ta1,tb1;reg [1:0] da1,db1;
always @(posedge clk or negedge rst_n) begin
if(!rst_n) begin pending_a<=0;pending_b<=0;joined<=0;result<=0;ta<=0;tag_b<=0;da<=0;db<=0;end
else begin joined<=0;
if(flush) begin pending_a<=0;pending_b<=0;result<=0;ta<=0;tag_b<=0;da<=0;db<=0;end
else begin
va1=av||pending_a;vb1=bv||pending_b;ta1=av?atag:ta;tb1=bv?btag:tag_b;da1=av?adata:da;db1=bv?bdata:db;
ta<=ta1;tag_b<=tb1;da<=da1;db<=db1;
if(va1 && vb1 && ta==tag_b) begin pending_a<=0;pending_b<=0;joined<=1;result<=da1^db1;end
else begin pending_a<=va1;pending_b<=vb1;end
end end end
endmodule
