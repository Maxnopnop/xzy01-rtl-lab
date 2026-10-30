module tb;reg clk=0,rst_n=1;reg feed=0; reg [1:0] symbol=0; reg flush=0;wire active; wire escaped; wire [1:0] work_sum; wire [1:0] work_count; wire [1:0] last_sum; wire [1:0] last_count; wire completed;
reg [16:0] vectors[0:6854];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
escape_frame D(.clk(clk), .rst_n(rst_n), .feed(feed), .symbol(symbol), .flush(flush), .active(active), .escaped(escaped), .work_sum(work_sum), .work_count(work_count), .last_sum(last_sum), .last_count(last_count), .completed(completed));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<6855;i=i+1) begin {clk,rst_n,feed,symbol,flush}=vectors[i][16:11];#2;checks=checks+1;
if({active,escaped,work_sum,work_count,last_sum,last_count,completed} !== vectors[i][10:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][10:0],{active,escaped,work_sum,work_count,last_sum,last_count,completed});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
