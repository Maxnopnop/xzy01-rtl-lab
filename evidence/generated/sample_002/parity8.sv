module parity8(
    input  wire [7:0] a,
    output wire       parity
);
    assign parity = ^a;
endmodule
