module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    output walk_left,
    output walk_right
);

    typedef enum logic {
        WALK_LEFT,
        WALK_RIGHT
    } state_e;

    state_e state_d, state_q;

    always_comb begin
        state_d = state_q;
        case (state_q)
            WALK_LEFT: begin
                if (bump_left) begin
                    state_d = WALK_RIGHT;
                end
            end
            WALK_RIGHT: begin
                if (bump_right) begin
                    state_d = WALK_LEFT;
                end
            end
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state_q <= WALK_LEFT;
        end else begin
            state_q <= state_d;
        end
    end

    assign walk_left  = (state_q == WALK_LEFT);
    assign walk_right = (state_q == WALK_RIGHT);

endmodule
