module counter_12 (
    input  logic       rst_n,
    input  logic       clk,
    input  logic       valid_count,
    output logic [3:0] out
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            out <= 4'b0000;
        else if (valid_count) begin
            if (out == 4'd11)
                out <= 4'b0000;
            else
                out <= out + 4'd1;
        end
    end

endmodule
