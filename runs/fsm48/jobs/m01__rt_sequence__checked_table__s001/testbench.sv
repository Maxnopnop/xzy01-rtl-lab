// Independently authored fixed-vector harness, dev10-v1. Original TB retained in upstream/.
`timescale 1ns/1ps
module tb;
reg rst_n;
reg data_in;
wire sequence_detected;
reg clk=0; reg valid_pre; reg [0:0] expected_pre;
reg [0:0] expected;
reg [4:0] vectors[0:919];
integer i, checks=0, errors=0, fd;
reg [255:0] nonce;
sequence_detector dut(.clk(clk), .rst_n(rst_n), .data_in(data_in), .sequence_detected(sequence_detected));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("rt_sequence.hex",vectors);
for(i=0;i<920;i=i+1) begin
{{rst_n,data_in}, expected_pre, expected, valid_pre}=vectors[i]; #2;
if(valid_pre) begin checks=checks+1; if({sequence_detected} !== expected_pre) errors=errors+1; end
clk=1; #2; checks=checks+1; if({sequence_detected} !== expected) errors=errors+1; clk=0; #2;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
