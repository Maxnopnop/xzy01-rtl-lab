module TopModule (
    input  logic clk,
    input  logic x,
    output logic z
);

    logic xor_ff = 1'b0;
    logic and_ff = 1'b0;
    logic or_ff  = 1'b0;

    always_ff @(posedge clk) begin
        xor_ff <= x ^ xor_ff;
        and_ff <= x & ~and_ff;
        or_ff  <= x | ~or_ff;
    end

    assign z = ~(xor_ff | and_ff | or_ff);

endmodule
