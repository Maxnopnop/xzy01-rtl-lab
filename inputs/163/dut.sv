module TopModule(
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] s,
    output logic       overflow
);
    logic [7:0] sum;
    assign sum = a + b;
    assign s = sum;

    assign overflow = (~a[7] & ~b[7] & sum[7]) | (a[7] & b[7] & ~sum[7]);
endmodule
