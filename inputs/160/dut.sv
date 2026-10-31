module TopModule (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] s,
    output logic overflow
);

    logic signed [8:0] sum_ext; // Extend by one bit to detect overflow

    always_comb begin
        sum_ext = $signed(a) + $signed(b);  // Perform signed addition
        s = sum_ext[7:0];                   // Assign the lower 8 bits to s
        overflow = (sum_ext[8] != sum_ext[7]); // Check overflow
    end

endmodule
