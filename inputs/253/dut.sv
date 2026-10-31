module TopModule(
    input  logic clk,
    input  logic x,
    output logic z
);
    // Flip-flop states
    logic q_xor, q_and, q_or;

    // Compute next states for each flip-flop
    logic d_xor, d_and, d_or;

    assign d_xor = x ^ q_xor;
    assign d_and = x & ~q_and;
    assign d_or  = x | ~q_or;

    // D Flip-Flops with initial reset-to-zero at elaboration time
    always_ff @(posedge clk) begin
        q_xor <= d_xor;
        q_and <= d_and;
        q_or  <= d_or;
    end

    // Output is NOR of all three FF outputs
    assign z = ~(q_xor | q_and | q_or);

endmodule
