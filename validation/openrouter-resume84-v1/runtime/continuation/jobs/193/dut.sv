module TopModule (
    input  clk,
    input  x,
    output z
);

    logic q_x = 1'b0;
    logic q_and = 1'b0;
    logic q_or = 1'b0;

    always @(posedge clk) begin
        q_x   <= x ^ q_x;
        q_and <= x & ~q_and;
        q_or  <= x | ~q_or;
    end

    assign z = ~(q_x | q_and | q_or);

endmodule
