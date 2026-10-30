module TopModule (
    input  clk,
    input  areset,
    input  x,
    output logic z
);

    logic seen_one;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            seen_one <= 1'b0;
            z        <= 1'b0;
        end else if (!seen_one) begin
            if (x) begin
                seen_one <= 1'b1;
                z        <= 1'b1;
            end else begin
                z <= 1'b0;
            end
        end else begin
            z <= ~x;
        end
    end

endmodule
