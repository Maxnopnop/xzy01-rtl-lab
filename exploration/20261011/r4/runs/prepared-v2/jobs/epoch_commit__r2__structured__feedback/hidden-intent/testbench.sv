module tb;reg clk=0,rst_n=1;reg write=0; reg slot=0; reg [1:0] data=0; reg commit=0; reg abort_tx=0; reg read_slot=0;wire [1:0] visible; wire [1:0] dirty; wire committed;
reg [13:0] vectors[0:6624];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
epoch_commit D(.clk(clk), .rst_n(rst_n), .write(write), .slot(slot), .data(data), .commit(commit), .abort_tx(abort_tx), .read_slot(read_slot), .visible(visible), .dirty(dirty), .committed(committed));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<6625;i=i+1) begin {clk,rst_n,write,slot,data,commit,abort_tx,read_slot}=vectors[i][13:5];#2;checks=checks+1;
if({visible,dirty,committed} !== vectors[i][4:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][4:0],{visible,dirty,committed});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
