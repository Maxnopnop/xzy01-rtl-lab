module TopModule (
    input  clk,
    input  areset,
    input  in,
    output reg out
);

    reg state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= 1'b1;
        else if (state)
            state <= in;
        else
            state <= ~in;
    end

    always_comb begin
        out = ~state;
    end

endmodule
