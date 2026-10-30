module tb; reg clk=0;reg rst_n=1;reg din=0;wire q;reg [3:0] vectors[0:90971];integer i,count=0,errors=0,fd;reg [255:0] nonce;
request_delay D(.clk(clk),.rst_n(rst_n),.din(din),.q(q));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish; $readmemb("events.bin",vectors);
for(i=0;i<90972;i=i+1) begin {clk,rst_n,din}=vectors[i][3:1]; #2;count=count+1;
if(q !== vectors[i][0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d clk=%0d reset=%0d input=%0d expected=%0d observed=%0b",i,clk,rst_n,din,vectors[i][0],q);end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,count,errors);$fclose(fd);$finish;end endmodule
