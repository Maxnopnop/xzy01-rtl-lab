module tb;reg clk=0,rst_n=1;reg req0=0; reg req1=0; reg retire=0;wire grant0; wire grant1;
reg [6:0] vectors[0:115];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
rotating_owner D(.clk(clk), .rst_n(rst_n), .req0(req0), .req1(req1), .retire(retire), .grant0(grant0), .grant1(grant1));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<116;i=i+1) begin {clk,rst_n,req0,req1,retire}=vectors[i][6:2];#2;checks=checks+1;
if({grant0,grant1} !== vectors[i][1:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][1:0],{grant0,grant1});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
