module decoder3 (
    input  wire [2:0] index,
    input  wire       en,
    output wire [7:0] y
);
    assign y = en ? (8'b00000001 << index) : 8'b00000000;
endmodule
