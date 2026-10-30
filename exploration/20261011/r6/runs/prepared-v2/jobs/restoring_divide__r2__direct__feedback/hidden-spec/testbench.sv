module tb;reg clk=0,rst_n=1;reg abort=0; reg start=0; reg advance=0; reg [3:0] numerator=0; reg [3:0] denominator=0;wire busy; wire done; wire [3:0] quotient; wire [3:0] remainder;
reg [22:0] vectors[0:9789];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
restoring_divide D(.clk(clk), .rst_n(rst_n), .abort(abort), .start(start), .advance(advance), .numerator(numerator), .denominator(denominator), .busy(busy), .done(done), .quotient(quotient), .remainder(remainder));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<9790;i=i+1) begin {clk,rst_n,abort,start,advance,numerator,denominator}=vectors[i][22:10];#2;checks=checks+1;
if({busy,done,quotient,remainder} !== vectors[i][9:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][9:0],{busy,done,quotient,remainder});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
