// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
reg rst_n;
reg [3:0] mul_a;
reg [3:0] mul_b;
wire [7:0] mul_out;
reg clk=0; reg valid_pre; reg [7:0] expected_pre;
reg [7:0] expected;
reg [25:0] vectors[0:511];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
multi_pipe_4bit dut(.clk(clk), .rst_n(rst_n), .mul_a(mul_a), .mul_b(mul_b), .mul_out(mul_out));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("rt_pipeline.hex",vectors);
for(i=0;i<512;i=i+1) begin
{{rst_n,mul_a,mul_b}, expected_pre, expected, valid_pre}=vectors[i]; #2;
if(valid_pre) begin checks=checks+1; if({mul_out} !== expected_pre) errors=errors+1; end
clk=1; #2; checks=checks+1; if({mul_out} !== expected) errors=errors+1; clk=0; #2;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
