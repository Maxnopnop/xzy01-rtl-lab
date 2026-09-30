module adder8 (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [8:0] sum
);
    assign sum = {1'b0, a} + {1'b0, b};
endmodule
