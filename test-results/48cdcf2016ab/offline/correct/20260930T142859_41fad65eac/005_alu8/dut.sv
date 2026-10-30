module alu8(input wire [7:0] a, b, input wire [2:0] op, output reg [7:0] y);
always @* case(op) 0:y=a+b; 1:y=a-b; 2:y=a&b; 3:y=a|b; 4:y=a^b; 5:y=a<<1; 6:y=a>>1; 7:y=(a<b); endcase
endmodule
