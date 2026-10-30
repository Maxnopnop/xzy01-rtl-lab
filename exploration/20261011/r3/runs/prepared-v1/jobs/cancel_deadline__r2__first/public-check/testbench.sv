module tb;reg clk=0,rst_n=1;reg req=0; reg cancel=0; reg finish=0;wire busy; wire accepted; wire completed; wire cancelled; wire expired;
reg [9:0] vectors[0:125];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
cancel_deadline D(.clk(clk), .rst_n(rst_n), .req(req), .cancel(cancel), .finish(finish), .busy(busy), .accepted(accepted), .completed(completed), .cancelled(cancelled), .expired(expired));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<126;i=i+1) begin {clk,rst_n,req,cancel,finish}=vectors[i][9:5];#2;checks=checks+1;
if({busy,accepted,completed,cancelled,expired} !== vectors[i][4:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][4:0],{busy,accepted,completed,cancelled,expired});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
