module TopModule (
    input  logic clk,
    input  logic x,
    output logic z
);

    logic [2:0] q = 3'b000;

    always_ff @(posedge clk) begin
        q[0] <= x ^ q[0];
        q[1] <= x & ~q[1];
        q[2] <= x | ~q[2];
    end

    always_comb begin
        z = ~|q;
    end

endmodule
