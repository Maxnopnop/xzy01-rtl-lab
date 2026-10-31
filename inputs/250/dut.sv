module TopModule(
    input clk,
    input x,
    output z
);

    // Internal flip-flop state registers
    reg ff_xor;
    reg ff_and;
    reg ff_or;

    // Initialize flip-flops to zero
    initial begin
        ff_xor = 0;
        ff_and = 0;
        ff_or = 0;
    end

    // Flip-flops update logic
    always @(posedge clk) begin
        ff_xor <= x ^ ff_xor;             // XOR with previous state
        ff_and <= x & ~ff_and;            // AND with NOT of previous state
        ff_or <= x | ~ff_or;              // OR with NOT of previous state
    end

    // NOR gate output
    assign z = ~(ff_xor | ff_and | ff_or);

endmodule
