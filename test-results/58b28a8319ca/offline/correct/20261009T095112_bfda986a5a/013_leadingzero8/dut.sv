module leadingzero8(input wire [7:0] a, output reg [3:0] count);
integer i; reg seen; always @* begin count=0; seen=0; for(i=7;i>=0;i=i-1) begin if(a[i]) seen=1; if(!seen) count=count+1; end end
endmodule
