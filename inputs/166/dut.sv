module TopModule (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] s,
    output logic       overflow
);
    logic [8:0] sum_ext;

    always_comb begin
        sum_ext = {a[7], a} + {b[7], b};
        s = sum_ext[7:0];
        overflow = (a[7] == b[7]) && (s[7] != a[7]);
    end
endmodule
