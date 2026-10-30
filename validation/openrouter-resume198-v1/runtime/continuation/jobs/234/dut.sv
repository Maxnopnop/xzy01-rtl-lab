module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);

    logic state;
    logic next_state;

    always_comb begin
        next_state = state;

        if (state == 1'b0) begin
            if (bump_left)
                next_state = 1'b1;
        end else begin
            if (bump_right)
                next_state = 1'b0;
        end
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= 1'b0;
        else
            state <= next_state;
    end

    always_comb begin
        walk_left  = ~state;
        walk_right = state;
    end

endmodule
