module TopModule(
    input  [7:0] a,
    input  [7:0] b,
    input  [7:0] c,
    input  [7:0] d,
    output [7:0] min
);
    wire [7:0] min_ab;
    wire [7:0] min_cd;
    wire [7:0] min_abcd;

    assign min_ab = (a < b) ? a : b;
    assign min_cd = (c < d) ? c : d;
    assign min_abcd = (min_ab < min_cd) ? min_ab : min_cd;

    assign min = min_abcd;
endmodule
