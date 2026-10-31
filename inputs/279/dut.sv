module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);

    typedef enum logic [1:0] {
        WalkLeft,
        WalkRight
    } state_e;

    state_e state, next_state;

    // State transition and output logic
    always_comb begin
        // Default values
        next_state = state;
        walk_left = 0;
        walk_right = 0;

        case (state)
            WalkLeft: begin
                // Currently walking left
                walk_left = 1;
                if (bump_left) begin
                    next_state = WalkRight;
                end
            end

            WalkRight: begin
                // Currently walking right
                walk_right = 1;
                if (bump_right) begin
                    next_state = WalkLeft;
                end
            end
        endcase
    end

    // State register update
    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WalkLeft;
        end else begin
            state <= next_state;
        end
    end

endmodule
