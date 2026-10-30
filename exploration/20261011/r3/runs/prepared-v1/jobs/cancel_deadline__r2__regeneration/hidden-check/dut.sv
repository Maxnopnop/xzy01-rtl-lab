module cancel_deadline (
    input  logic clk,
    input  logic rst_n,
    input  logic req,
    input  logic cancel,
    input  logic finish,
    output logic busy,
    output logic accepted,
    output logic completed,
    output logic cancelled,
    output logic expired
);

    logic [1:0] remaining;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy      <= 1'b0;
            remaining <= 2'd0;
            accepted  <= 1'b0;
            completed <= 1'b0;
            cancelled <= 1'b0;
            expired   <= 1'b0;
        end else begin
            accepted  <= 1'b0;
            completed <= 1'b0;
            cancelled <= 1'b0;
            expired   <= 1'b0;

            if (!busy) begin
                if (req) begin
                    busy      <= 1'b1;
                    remaining <= 2'd3;
                    accepted  <= 1'b1;
                end
            end else if (cancel) begin
                busy      <= 1'b0;
                remaining <= 2'd0;
                cancelled <= 1'b1;
            end else if (finish) begin
                busy      <= 1'b0;
                remaining <= 2'd0;
                completed <= 1'b1;
            end else if (remaining == 2'd1) begin
                busy      <= 1'b0;
                remaining <= 2'd0;
                expired   <= 1'b1;
            end else begin
                remaining <= remaining - 2'd1;
            end
        end
    end

endmodule
