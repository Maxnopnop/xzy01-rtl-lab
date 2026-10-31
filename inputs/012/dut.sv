module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    // State encoding
    typedef enum logic [1:0] {
        S_RESET, // Reset state, output 0
        S_0,     // State 0: output input bits unchanged
        S_1      // State 1: output complemented bits
    } state_e;

    state_e state_q, state_d;

    // Next state logic
    always_comb begin
        case (state_q)
            S_RESET: begin
                if (x)
                    state_d = S_1;
                else
                    state_d = S_0;
            end
            S_0: begin
                if (x)
                    state_d = S_1;
                else
                    state_d = S_0;
            end
            S_1: begin
                if (x)
                    state_d = S_1;
                else
                    state_d = S_0;
            end
            default: state_d = S_RESET;
        endcase
    end

    // Output logic (Moore: depends only on state)
    always_comb begin
        case (state_q)
            S_RESET: z = 1'b0;
            S_0:     z = 1'b0;
            S_1:     z = 1'b1;
            default: z = 1'b0;
        endcase
    end

    // Sequential logic with asynchronous active-high reset
    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state_q <= S_RESET;
        else
            state_q <= state_d;
    end

endmodule
