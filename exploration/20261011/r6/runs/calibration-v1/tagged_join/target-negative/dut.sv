module tagged_join(input clk,rst_n,clear,a_valid,input [1:0] a_tag,a_data,input b_valid,input [1:0] b_tag,b_data,input take,output reg a_full,b_full,out_valid,output reg [1:0] out_tag,output reg [3:0] out_data);
reg [1:0] at,ad,bt,bd;
always @(posedge clk or negedge rst_n)begin
 if(!rst_n || clear)begin a_full<=0;b_full<=0;out_valid<=0;out_tag<=0;out_data<=0;at<=0;ad<=0;bt<=0;bd<=0;end
 else begin
 if(!a_full && a_valid)begin a_full<=1;at<=a_tag;ad<=a_data;end
 if(!b_full && b_valid)begin b_full<=1;bt<=b_tag;bd<=b_data;end
 if(take)out_valid<=0;
 if(a_full && b_full)begin
 if(at>bt)a_full<=0;else if(bt<at)b_full<=0;
 else if(!out_valid || take)begin a_full<=0;b_full<=0;out_valid<=1;out_tag<=at;out_data<={ad,bd};end
 end
 end
end
endmodule
