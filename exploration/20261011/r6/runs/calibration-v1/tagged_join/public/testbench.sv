module tb;reg clk=0,rst_n=1;reg clear=0; reg a_valid=0; reg [1:0] a_tag=0; reg [1:0] a_data=0; reg b_valid=0; reg [1:0] b_tag=0; reg [1:0] b_data=0; reg take=0;wire a_full; wire b_full; wire out_valid; wire [1:0] out_tag; wire [3:0] out_data;
reg [22:0] vectors[0:34];integer i,checks=0,errors=0,fd;reg [255:0] nonce;
tagged_join D(.clk(clk), .rst_n(rst_n), .clear(clear), .a_valid(a_valid), .a_tag(a_tag), .a_data(a_data), .b_valid(b_valid), .b_tag(b_tag), .b_data(b_data), .take(take), .a_full(a_full), .b_full(b_full), .out_valid(out_valid), .out_tag(out_tag), .out_data(out_data));
initial begin if(!$value$plusargs("nonce=%s",nonce)) $finish;$readmemh("vectors.hex",vectors);
for(i=0;i<35;i=i+1) begin {clk,rst_n,clear,a_valid,a_tag,a_data,b_valid,b_tag,b_data,take}=vectors[i][22:9];#2;checks=checks+1;
if({a_full,b_full,out_valid,out_tag,out_data} !== vectors[i][8:0]) begin errors=errors+1;if(errors<=8)$display("MISMATCH event=%0d expected=%0d observed=%0b",i,vectors[i][8:0],{a_full,b_full,out_valid,out_tag,out_data});end end
fd=$fopen("verdict.txt","w");$fdisplay(fd,"RTL_LAB_V1 %0s checks=%0d errors=%0d",nonce,checks,errors);$fclose(fd);$finish;end endmodule
