module tb;reg clk=0,rst_n=1;reg free_req=0; reg [1:0] release_id=0; reg allocate=0;wire [3:0] occupied; wire [1:0] hint; wire [1:0] last_alloc; wire alloc_valid; wire rejected;
reg [15:0] vectors[0:57];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
masked_ring_alloc D(.clk(clk), .rst_n(rst_n), .free_req(free_req), .release_id(release_id), .allocate(allocate), .occupied(occupied), .hint(hint), .last_alloc(last_alloc), .alloc_valid(alloc_valid), .rejected(rejected));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<58;i=i+1) begin {clk,rst_n,free_req,release_id,allocate}=vectors[i][15:10];#2;checks=checks+1;
if({occupied,hint,last_alloc,alloc_valid,rejected} !== vectors[i][9:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][9:0],{occupied,hint,last_alloc,alloc_valid,rejected});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
