module TopModule (
    input  logic clk,
    input  logic x,
    output logic z
);
    // Declare flip-flop internal signals
    logic xor_ff_q, and_ff_q, or_ff_q;

    // XOR gate input signals
    logic xor_in2;

    // AND gate input signals
    logic and_in2;

    // OR gate input signals
    logic or_in2;

    // Internal wire for NOR gate output
    logic nor_out;

    // Input logics for XOR, AND and OR gates
    always_comb begin
        xor_in2 = xor_ff_q;
        and_in2 = ~and_ff_q;
        or_in2  = ~or_ff_q;
    end

    // Sequential logic for D flip-flops
    always_ff @(posedge clk) begin
        xor_ff_q <= x ^ xor_in2;
        and_ff_q <= x & and_in2;
        or_ff_q  <= x | or_in2;
    end

    // Combinational logic for 3-input NOR gate
    assign nor_out = ~(xor_ff_q | and_ff_q | or_ff_q);

    // Output assignment
    assign z = nor_out;

endmodule
