module TopModule (
    input  logic [3:0] in,
    output logic [3:0] out_both,
    output logic [3:0] out_any,
    output logic [3:0] out_different
);

    always_comb begin
        out_both      = 4'b0000;
        out_any       = 4'b0000;
        out_different = 4'b0000;

        out_both[2:0] = in[2:0] & in[3:1];
        out_any[3:1]  = in[3:1] | in[2:0];

        out_different[2:0] = in[2:0] ^ in[3:1];
        out_different[3]   = in[3] ^ in[0];
    end

endmodule
