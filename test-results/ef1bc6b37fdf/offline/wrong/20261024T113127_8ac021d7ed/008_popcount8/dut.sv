module popcount8(input wire [7:0] a, output reg [3:0] count);
integer i; always @* begin count=0; for(i=0;i<7;i=i+1) count=count+a[i]; end
endmodule
