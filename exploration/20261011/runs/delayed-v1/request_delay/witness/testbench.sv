`timescale 1ns/1ps
module tb;
reg clk=0, rst_n, din; wire q;
reg pre, post, valid_pre, valid_post;
reg [5:0] vectors[0:12];
integer i, checks=0, errors=0, fd; reg [255:0] nonce;
request_delay dut(.clk(clk), .rst_n(rst_n), .din(din), .q(q));
initial begin
if (!$value$plusargs("nonce=%s",nonce)) $fatal(1,"nonce missing");
$readmemh("agreement.hex",vectors);
for(i=0;i<13;i=i+1) begin
{rst_n,din,pre,post,valid_pre,valid_post}=vectors[i]; #2;
if(valid_pre) begin checks=checks+1; if(q !== pre) begin
errors=errors+1; if(errors<=5) $display("MISMATCH cycle=%0d phase=pre reset=%0d input=%0d expected=%0d observed=%0d",i,rst_n,din,pre,q); end end
clk=1; #2;
if(valid_post) begin checks=checks+1; if(q !== post) begin
errors=errors+1; if(errors<=5) $display("MISMATCH cycle=%0d phase=post reset=%0d input=%0d expected=%0d observed=%0d",i,rst_n,din,post,q); end end
clk=0; #2;
end
fd=$fopen("verdict.txt","w");
$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);
$fclose(fd); $finish;
end
endmodule
