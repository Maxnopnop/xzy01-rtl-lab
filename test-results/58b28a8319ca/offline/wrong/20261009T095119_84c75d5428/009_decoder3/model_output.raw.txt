module decoder3(input wire [2:0] index, input wire en, output wire [7:0] y);
assign y=8'b1<<index;
endmodule
