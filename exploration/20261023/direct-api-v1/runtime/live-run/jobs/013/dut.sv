module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    typedef enum logic [1:0] {
        S_INIT = 2'b00,
        S_ONE  = 2'b01,
        S_ZERO = 2'b10
    } state_t;

    state_t state, next_state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= S_INIT;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            S_INIT: begin
                if (x)
                    next_state = S_ONE;
                else
                    next_state = S_INIT;
            end
            S_ONE: begin
                if (x)
                    next_state = S_ZERO;
                else
                    next_state = S_ONE;
            end
            S_ZERO: begin
                if (x)
                    next_state = S_ZERO;
                else
                    next_state = S_ONE;
            end
            default: next_state = S_INIT;
        endcase
    end

    always_comb begin
        case (state)
            S_ONE:   z = 1'b1;
            default: z = 1'b0;
        endcase
    end

endmodule
