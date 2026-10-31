module TopModule(
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    typedef enum logic [0:0] {
        S0, // Copy input bits
        S1  // After first 1, invert bits
    } state_t;

    state_t state, next_state;

    // Output logic
    always_comb begin
        case (state)
            S0: z = x;
            S1: z = ~x;
            default: z = 1'b0;
        endcase
    end

    // State transition logic
    always_comb begin
        case (state)
            S0: next_state = (x == 1'b1) ? S1 : S0;
            S1: next_state = S1;
            default: next_state = S0;
        endcase
    end

    // State register with asynchronous reset (active high)
    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= S0;
        else
            state <= next_state;
    end

endmodule
