module TopModule (
    input logic clk,
    input logic areset,
    input logic bump_left,
    input logic bump_right,
    output logic walk_left,
    output logic walk_right
);
    typedef enum logic [1:0] {
        STATE_LEFT = 2'b01,
        STATE_RIGHT = 2'b10
    } state_t;

    state_t state, next_state;

    // State transition logic
    always_comb begin
        case (state)
            STATE_LEFT: begin
                if (bump_left) 
                    next_state = STATE_RIGHT;
                else 
                    next_state = STATE_LEFT;
            end
            STATE_RIGHT: begin
                if (bump_right) 
                    next_state = STATE_LEFT;
                else 
                    next_state = STATE_RIGHT;
            end
            default: next_state = STATE_LEFT;
        endcase
    end

    // State update logic
    always_ff @(posedge clk or posedge areset) begin
        if (areset) 
            state <= STATE_LEFT;  // Reset to walking left
        else 
            state <= next_state;
    end

    // Output logic
    always_comb begin
        case (state)
            STATE_LEFT: begin
                walk_left = 1;
                walk_right = 0;
            end
            STATE_RIGHT: begin
                walk_left = 0;
                walk_right = 1;
            end
            default: begin
                walk_left = 1;
                walk_right = 0;
            end
        endcase
    end

endmodule
