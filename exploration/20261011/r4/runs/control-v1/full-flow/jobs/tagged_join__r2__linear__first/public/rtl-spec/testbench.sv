module tb;reg clk=0,rst_n=1;reg av=0; reg atag=0; reg [1:0] adata=0; reg bv=0; reg btag=0; reg [1:0] bdata=0; reg flush=0;wire pending_a; wire pending_b; wire joined; wire [1:0] result;
reg [15:0] vectors[0:45];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
tagged_join D(.clk(clk), .rst_n(rst_n), .av(av), .atag(atag), .adata(adata), .bv(bv), .btag(btag), .bdata(bdata), .flush(flush), .pending_a(pending_a), .pending_b(pending_b), .joined(joined), .result(result));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<46;i=i+1) begin {clk,rst_n,av,atag,adata,bv,btag,bdata,flush}=vectors[i][15:5];#2;checks=checks+1;
if({pending_a,pending_b,joined,result} !== vectors[i][4:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][4:0],{pending_a,pending_b,joined,result});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
