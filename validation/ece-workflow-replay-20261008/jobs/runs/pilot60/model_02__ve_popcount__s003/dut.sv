module TopModule (
    input  logic [254:0] in,
    output logic [7:0]   out
);
    integer i;
    always_comb begin
        out = '0;
        for (i = 0; i < 255; i = i + 1)
            out = out + in[i];
    end
endmodule
