module tb;reg clk=0,rst_n=1;reg submit=0; reg [1:0] refund=0; reg [1:0] cost=0;wire [2:0] credit; wire accepted; wire rejected; wire can_pay;
reg [12:0] vectors[0:55];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
refund_credit D(.clk(clk), .rst_n(rst_n), .submit(submit), .refund(refund), .cost(cost), .credit(credit), .accepted(accepted), .rejected(rejected), .can_pay(can_pay));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<56;i=i+1) begin {clk,rst_n,submit,refund,cost}=vectors[i][12:6];#2;checks=checks+1;
if({credit,accepted,rejected,can_pay} !== vectors[i][5:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][5:0],{credit,accepted,rejected,can_pay});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
