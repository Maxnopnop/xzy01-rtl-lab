// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
reg load;
reg [1:0] ena;
reg [99:0] data;
wire [99:0] q;
reg clk=0; reg valid_pre; reg [99:0] expected_pre;
reg [99:0] expected;
reg [303:0] vectors[0:419];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
TopModule dut(.clk(clk), .load(load), .ena(ena), .data(data), .q(q));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("ve_rotate.hex",vectors);
for(i=0;i<420;i=i+1) begin
{{load,ena,data}, expected_pre, expected, valid_pre}=vectors[i]; #2;
if(valid_pre) begin checks=checks+1; if({q} !== expected_pre) errors=errors+1; end
clk=1; #2; checks=checks+1; if({q} !== expected) errors=errors+1; clk=0; #2;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
