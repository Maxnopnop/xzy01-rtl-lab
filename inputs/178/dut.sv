module TopModule (
    input  logic [2:0] vec,
    output logic [2:0] outv,
    output logic o2,
    output logic o1,
    output logic o0
);
    // Pass the input vector directly to the output vector
    assign outv = vec;

    // Assign each bit of the input vector to individual output bits
    assign o2 = vec[2];
    assign o1 = vec[1];
    assign o0 = vec[0];
endmodule
