module TopModule (
    input  logic clk,
    input  logic x,
    output logic z
);

    logic xor_q = 1'b0;
    logic and_q = 1'b0;
    logic or_q  = 1'b0;

    always_ff @(posedge clk) begin
        xor_q <= x ^ xor_q;
        and_q <= x & ~and_q;
        or_q  <= x | ~or_q;
    end

    assign z = ~(xor_q | and_q | or_q);

endmodule
