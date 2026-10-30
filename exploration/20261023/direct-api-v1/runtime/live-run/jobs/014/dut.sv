module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    typedef enum logic [1:0] {
        INIT = 2'b00,
        ONE  = 2'b01,
        ZERO = 2'b10
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            INIT: next_state = x ? ONE : INIT;
            ONE:  next_state = x ? ZERO : ONE;
            ZERO: next_state = x ? ZERO : ONE;
            default: next_state = INIT;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= INIT;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            ONE:    z = 1'b1;
            default: z = 1'b0;
        endcase
    end

endmodule
