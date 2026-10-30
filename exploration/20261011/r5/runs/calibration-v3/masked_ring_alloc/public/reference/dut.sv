module masked_ring_alloc(input clk,rst_n,free_req,input [1:0] release_id,input allocate,output reg [3:0] occupied,output reg [1:0] hint,last_alloc,output reg alloc_valid,rejected);
reg [3:0] available_mask;integer j,k,chosen;
always @(posedge clk or negedge rst_n) begin
if(!rst_n)begin occupied<=0;hint<=0;last_alloc<=0;alloc_valid<=0;rejected<=0;end
else begin
available_mask=occupied;if(free_req)available_mask[release_id]=0;
chosen=-1;for(j=0;j<4;j=j+1)begin k=(hint+j)%4;if(!available_mask[k] && chosen==-1)chosen=k;end
alloc_valid<=0;rejected<=0;
if(allocate)begin if(chosen==-1)rejected<=1;else begin available_mask[chosen]=1;last_alloc<=chosen;hint<=(chosen+1)%4;alloc_valid<=1;end end
occupied<=available_mask;
end end
endmodule
