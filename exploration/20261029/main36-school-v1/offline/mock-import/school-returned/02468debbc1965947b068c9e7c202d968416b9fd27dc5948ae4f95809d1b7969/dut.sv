module TopModule(
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic [7:0] c,
    input  logic [7:0] d,
    output logic [7:0] min
);
    always_comb begin
        min = a; // Assume a is the minimum initially
        if (b < min) min = b;
        if (c < min) min = c;
        if (d < min) min = d;
    end
endmodule
