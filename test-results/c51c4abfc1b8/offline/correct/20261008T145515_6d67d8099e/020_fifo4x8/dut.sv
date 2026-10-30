module fifo4x8(input wire clk, rst, wr_en, rd_en, input wire [7:0] wdata, output wire full, empty, output reg [2:0] count, output wire [7:0] rdata);
reg [7:0] mem [0:3]; reg [1:0] wp,rp;
wire push=wr_en && !full; wire pop=rd_en && !empty;
assign full=(count==4); assign empty=(count==0); assign rdata=empty ? 8'b0 : mem[rp];
always @(posedge clk) if(rst) begin wp<=0; rp<=0; count<=0; end else begin
 if(push) begin mem[wp]<=wdata; wp<=wp+1; end
 if(pop) rp<=rp+1;
 case({push,pop}) 2'b10:count<=count+1; 2'b01:count<=count-1; default:count<=count; endcase
end
endmodule
