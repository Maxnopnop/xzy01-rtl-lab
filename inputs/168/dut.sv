module TopModule (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] s,
    output logic       overflow
);

    logic [8:0] sum_ext;

    assign sum_ext  = {a[7], a} + {b[7], b};
    assign s        = sum_ext[7:0];
    assign overflow = (~(a[7] ^ b[7])) & (s[7] ^ a[7]);

endmodule
