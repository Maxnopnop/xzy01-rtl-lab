module restoring_divide(input clk,rst_n,abort,start,advance,input [3:0] numerator,denominator,output reg busy,done,output reg [3:0] quotient,remainder);
reg [3:0] n,d,q;reg [4:0] rem;reg [2:0] left;wire [4:0] trial={rem[3:0],n[3]};wire bitq=trial>={1'b0,d};wire [4:0] nextrem=bitq?trial-{1'b0,d}:trial;wire [3:0] nextq={q[2:0],bitq};
always @(posedge clk or negedge rst_n)begin
 if(!rst_n || abort)begin busy<=0;done<=0;quotient<=0;remainder<=0;n<=0;d<=0;q<=0;rem<=0;left<=0;end
 else begin done<=0;
 if(!busy)begin if(start)begin if(denominator==0)begin busy<=0;done<=1;quotient<=15;remainder<=numerator;end else begin busy<=1;n<=numerator;d<=denominator;q<=0;rem<=0;left<=4;end end end
 else if(advance)begin n<={n[2:0],1'b0};q<=nextq;rem<=nextrem;left<=left-1;if(left==1)begin quotient<=nextq;remainder<=nextrem[3:0];busy<=0;done<=1;end end
 end
end
endmodule
