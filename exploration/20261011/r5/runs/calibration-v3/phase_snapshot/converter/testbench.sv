module tb;reg clk=0,rst_n=1;reg capture=0; reg clear_sample=0; reg [1:0] data=0; reg publish=0;wire [1:0] sampled; wire [1:0] visible; wire published;
reg [11:0] vectors[0:9127];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
phase_snapshot D(.clk(clk), .rst_n(rst_n), .capture(capture), .clear_sample(clear_sample), .data(data), .publish(publish), .sampled(sampled), .visible(visible), .published(published));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<9128;i=i+1) begin {clk,rst_n,capture,clear_sample,data,publish}=vectors[i][11:5];#2;checks=checks+1;
if({sampled,visible,published} !== vectors[i][4:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][4:0],{sampled,visible,published});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
