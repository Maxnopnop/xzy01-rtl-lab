module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);

    typedef enum logic [0:0] {LEFT=1'b0, RIGHT=1'b1} state_t;
    state_t state, next_state;

    // State transition logic
    always_comb begin
        case (state)
            LEFT:  next_state = (bump_left | bump_right) ? RIGHT : LEFT;
            RIGHT: next_state = (bump_left | bump_right) ? LEFT : RIGHT;
            default: next_state = LEFT;
        endcase
    end

    // State register with asynchronous reset
    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= LEFT;
        else
            state <= next_state;
    end

    // Output logic (Moore machine outputs depend only on state)
    assign walk_left = (state == LEFT);
    assign walk_right = (state == RIGHT);

endmodule
