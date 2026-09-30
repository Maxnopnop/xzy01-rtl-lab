module edge_detector(
    input  wire clk,
    input  wire rst,
    input  wire din,
    output reg  pulse
);

    reg din_prev;

    always_ff @(posedge clk) begin
        if (rst) begin
            din_prev <= 1'b0;
            pulse    <= 1'b0;
        end else begin
            pulse    <= din & ~din_prev;
            din_prev <= din;
        end
    end

endmodule
