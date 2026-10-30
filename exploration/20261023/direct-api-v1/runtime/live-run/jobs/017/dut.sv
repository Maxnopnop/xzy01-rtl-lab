module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        WAIT_ONE,
        INVERT_OUT_ONE,
        INVERT_OUT_ZERO
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            WAIT_ONE: begin
                if (x)
                    next_state = INVERT_OUT_ONE;
                else
                    next_state = WAIT_ONE;
            end

            INVERT_OUT_ONE,
            INVERT_OUT_ZERO: begin
                if (x)
                    next_state = INVERT_OUT_ZERO;
                else
                    next_state = INVERT_OUT_ONE;
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
        z = (state == INVERT_OUT_ONE);
    end

endmodule
