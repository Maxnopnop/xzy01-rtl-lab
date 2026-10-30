// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
reg do_sub;
reg [7:0] a;
reg [7:0] b;
wire [7:0] out;
wire result_is_zero;

reg [8:0] expected;
reg [25:0] vectors[0:131071];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
TopModule dut(.do_sub(do_sub), .a(a), .b(b), .out(out), .result_is_zero(result_is_zero));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("ve_addsub.hex",vectors);
for(i=0;i<131072;i=i+1) begin
{{do_sub,a,b}, expected}=vectors[i]; #2; checks=checks+1; if({out,result_is_zero} !== expected) errors=errors+1;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
