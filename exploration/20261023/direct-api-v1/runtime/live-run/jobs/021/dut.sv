module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    typedef enum logic [1:0] {
        WAIT_ONE = 2'b00,
        COMP_ONE = 2'b01,
        COMP_ZERO = 2'b10
    } state_t;

    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            WAIT_ONE: begin
                if (x)
                    next_state = COMP_ONE;
                else
                    next_state = WAIT_ONE;
            end

            COMP_ONE: begin
                if (x)
                    next_state = COMP_ZERO;
                else
                    next_state = COMP_ONE;
            end

            COMP_ZERO: begin
                if (x)
                    next_state = COMP_ZERO;
                else
                    next_state = COMP_ONE;
            end

            default: next_state = WAIT_ONE;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= WAIT_ONE;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            COMP_ONE: z = 1'b1;
            default:  z = 1'b0;
        endcase
    end

endmodule
