module edge_detector (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output reg  pulse
);

    reg din_history;

    always_ff @(posedge clk) begin
        if (rst) begin
            din_history <= 1'b0;
            pulse       <= 1'b0;
        end else begin
            pulse       <= din & ~din_history;
            din_history <= din;
        end
    end

endmodule
