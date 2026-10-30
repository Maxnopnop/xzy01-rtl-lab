module tb;reg clk=0,rst_n=1;reg flush=0; reg issue=0; reg [1:0] issue_tag=0; reg finish=0; reg [1:0] finish_tag=0;wire [1:0] count; wire retired; wire [1:0] retired_tag;
reg [13:0] vectors[0:3353];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
ordered_retire D(.clk(clk), .rst_n(rst_n), .flush(flush), .issue(issue), .issue_tag(issue_tag), .finish(finish), .finish_tag(finish_tag), .count(count), .retired(retired), .retired_tag(retired_tag));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<3354;i=i+1) begin {clk,rst_n,flush,issue,issue_tag,finish,finish_tag}=vectors[i][13:5];#2;checks=checks+1;
if({count,retired,retired_tag} !== vectors[i][4:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][4:0],{count,retired,retired_tag});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
