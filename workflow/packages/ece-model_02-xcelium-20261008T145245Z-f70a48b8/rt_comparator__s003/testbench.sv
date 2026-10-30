// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
reg [2:0] A;
reg [2:0] B;
wire A_greater;
wire A_equal;
wire A_less;

reg [2:0] expected;
reg [8:0] vectors[0:63];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
comparator_3bit dut(.A(A), .B(B), .A_greater(A_greater), .A_equal(A_equal), .A_less(A_less));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("rt_comparator.hex",vectors);
for(i=0;i<64;i=i+1) begin
{{A,B}, expected}=vectors[i]; #2; checks=checks+1; if({A_greater,A_equal,A_less} !== expected) errors=errors+1;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
