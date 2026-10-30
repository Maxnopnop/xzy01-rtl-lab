module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic bump_left,
    input  logic bump_right,
    output logic walk_left,
    output logic walk_right
);

    logic direction;
    logic next_direction;

    always_comb begin
        next_direction = direction;
        if (!direction && bump_left)
            next_direction = 1'b1;
        else if (direction && bump_right)
            next_direction = 1'b0;
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            direction <= 1'b0;
        else
            direction <= next_direction;
    end

    always_comb begin
        walk_left  = ~direction;
        walk_right = direction;
    end

endmodule
