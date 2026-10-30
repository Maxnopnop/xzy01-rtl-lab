// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
reg [254:0] in;
wire [7:0] out;

reg [7:0] expected;
reg [262:0] vectors[0:1111];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
TopModule dut(.in(in), .out(out));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("ve_popcount.hex",vectors);
for(i=0;i<1112;i=i+1) begin
{{in}, expected}=vectors[i]; #2; checks=checks+1; if({out} !== expected) errors=errors+1;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
