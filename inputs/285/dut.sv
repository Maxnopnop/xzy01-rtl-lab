module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    output walk_left,
    output walk_right
);

    typedef enum logic {WALKING_LEFT, WALKING_RIGHT} state_t;
    state_t state, next_state;

    always_comb begin
        next_state = state;

        case (state)
            WALKING_LEFT: begin
                if (bump_left)
                    next_state = WALKING_RIGHT;
            end

            WALKING_RIGHT: begin
                if (bump_right)
                    next_state = WALKING_LEFT;
            end

            default: begin
                next_state = WALKING_LEFT;
            end
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= WALKING_LEFT;
        else
            state <= next_state;
    end

    always_comb begin
        walk_left  = (state == WALKING_LEFT);
        walk_right = (state == WALKING_RIGHT);
    end

endmodule
