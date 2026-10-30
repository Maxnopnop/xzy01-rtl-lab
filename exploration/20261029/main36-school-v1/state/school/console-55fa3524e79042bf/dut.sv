module TopModule (
    input  logic         clk,
    input  logic         load,
    input  logic [511:0] data,
    output logic [511:0] q
);

    logic [511:0] next_q;
    logic [511:0] left_cells;
    logic [511:0] right_cells;

    always_comb begin
        left_cells  = q >> 1;
        right_cells = q << 1;

        next_q = ((~left_cells) & q) |
                 ((~q) & right_cells) |
                 (q & (~right_cells));
    end

    always_ff @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
