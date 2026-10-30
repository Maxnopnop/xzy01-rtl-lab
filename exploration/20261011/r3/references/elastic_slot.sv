module elastic_slot(input clk,rst_n,in_valid,out_ready,input [1:0] in_data,output in_ready,out_valid,output [1:0] out_data);
reg occupied;reg [1:0] stored;
assign in_ready=rst_n && (!occupied || out_ready);
assign out_valid=rst_n && occupied;
assign out_data=rst_n?stored:2'b00;
always @(posedge clk or negedge rst_n) begin
 if(!rst_n) begin occupied<=0;stored<=0;end
 else if(in_valid && in_ready) begin occupied<=1;stored<=in_data;end
 else if(occupied && out_ready) begin occupied<=0;stored<=0;end
end
endmodule
