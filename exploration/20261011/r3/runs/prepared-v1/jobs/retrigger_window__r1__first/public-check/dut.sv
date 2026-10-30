module retrigger_window (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       trigger,
    input  logic       tick,
    input  logic       enable,
    input  logic [1:0] length,
    output logic       active,
    output logic [1:0] remaining,
    output logic       expired
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active    <= 1'b0;
            remaining <= 2'b00;
            expired   <= 1'b0;
        end else begin
            expired <= 1'b0;

            if (trigger) begin
                active    <= 1'b1;
                remaining <= (length == 2'b00) ? 2'b01 : length;
            end else if (active && enable && tick) begin
                if (remaining == 2'b01) begin
                    active    <= 1'b0;
                    remaining <= 2'b00;
                    expired   <= 1'b1;
                end else begin
                    remaining <= remaining - 2'b01;
                end
            end
        end
    end

endmodule
