module tb;reg clk=0,rst_n=1;reg in_valid=0; reg out_ready=0; reg [1:0] in_data=0;wire in_ready; wire out_valid; wire [1:0] out_data;
reg [9:0] vectors[0:100];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
elastic_slot D(.clk(clk), .rst_n(rst_n), .in_valid(in_valid), .out_ready(out_ready), .in_data(in_data), .in_ready(in_ready), .out_valid(out_valid), .out_data(out_data));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<101;i=i+1) begin {clk,rst_n,in_valid,out_ready,in_data}=vectors[i][9:4];#2;checks=checks+1;
if({in_ready,out_valid,out_data} !== vectors[i][3:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][3:0],{in_ready,out_valid,out_data});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
