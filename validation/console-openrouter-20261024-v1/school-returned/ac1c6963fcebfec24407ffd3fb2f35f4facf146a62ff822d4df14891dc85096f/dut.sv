module TopModule (
    input  logic [3:0] in,
    output logic [3:0] out_both,
    output logic [3:0] out_any,
    output logic [3:0] out_different
);

    assign out_both = in & (in >> 1);
    assign out_any = in | (in << 1);
    assign out_different = in ^ {in[0], in[3:1]};

endmodule
