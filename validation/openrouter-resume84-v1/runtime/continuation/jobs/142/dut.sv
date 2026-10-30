module TopModule (
    input  clk,
    input  areset,
    input  in,
    output out
);

    typedef enum logic {A, B} state_t;
    state_t state, next_state;

    always_comb begin
        next_state = state;
        case (state)
            A: begin
                if (in)
                    next_state = A;
                else
                    next_state = B;
            end
            B: begin
                if (in)
                    next_state = B;
                else
                    next_state = A;
            end
            default: next_state = B;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= B;
        else
            state <= next_state;
    end

    assign out = (state == B);

endmodule
