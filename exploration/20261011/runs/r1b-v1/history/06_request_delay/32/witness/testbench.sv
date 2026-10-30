module tb;reg clk=0;reg rst_n=1;reg din=0;wire q;integer errors=0;integer count=0;integer receipt;reg [8*128-1:0] nonce;
request_delay D(.clk(clk),.rst_n(rst_n),.din(din),.q(q));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;
clk=0; rst_n=0; din=0; #2; count=count+1; if(q !== 1'b0) errors=errors+1;
clk=1; #2; count=count+1; if(q !== 1'b0) errors=errors+1;
clk=0; rst_n=1; din=1; #2; count=count+1; if(q !== 1'b0) errors=errors+1;
clk=1; #2; count=count+1; if(q !== 1'b0) errors=errors+1;
receipt=$fopen("verdict.txt","w"); $fdisplay(receipt,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,count,errors);$fclose(receipt);$finish;end endmodule