module tb;reg clk=0,rst_n=1;reg trigger=0; reg tick=0; reg enable=0; reg [1:0] length=0;wire active; wire [1:0] remaining; wire expired;
reg [10:0] vectors[0:146];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
retrigger_window D(.clk(clk), .rst_n(rst_n), .trigger(trigger), .tick(tick), .enable(enable), .length(length), .active(active), .remaining(remaining), .expired(expired));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<147;i=i+1) begin {clk,rst_n,trigger,tick,enable,length}=vectors[i][10:4];#2;checks=checks+1;
if({active,remaining,expired} !== vectors[i][3:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][3:0],{active,remaining,expired});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
