module TopModule (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] s,
    output logic       overflow
);

    logic [8:0] sum;

    assign sum = {a[7], a} + {b[7], b};
    assign s = sum[7:0];
    assign overflow = (a[7] == b[7]) && (s[7] != a[7]);

endmodule
