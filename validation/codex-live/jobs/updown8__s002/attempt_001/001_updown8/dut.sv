module updown8 (
    input  wire       clk,
    input  wire       rst,
    input  wire       en,
    input  wire       up,
    output reg  [7:0] q
);

    always_ff @(posedge clk) begin
        if (rst)
            q <= 8'h00;
        else if (en) begin
            if (up)
                q <= q + 8'h01;
            else
                q <= q - 8'h01;
        end
    end

endmodule
