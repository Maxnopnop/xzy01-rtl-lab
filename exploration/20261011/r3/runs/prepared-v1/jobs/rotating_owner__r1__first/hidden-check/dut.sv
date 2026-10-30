module rotating_owner (
    input  logic clk,
    input  logic rst_n,
    input  logic req0,
    input  logic req1,
    input  logic retire,
    output logic grant0,
    output logic grant1
);

    logic prefer1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant0  <= 1'b0;
            grant1  <= 1'b0;
            prefer1 <= 1'b0;
        end else if (grant0) begin
            if (retire) begin
                prefer1 <= 1'b1;
                if (req1) begin
                    grant0 <= 1'b0;
                    grant1 <= 1'b1;
                end else if (req0) begin
                    grant0 <= 1'b1;
                    grant1 <= 1'b0;
                end else begin
                    grant0 <= 1'b0;
                    grant1 <= 1'b0;
                end
            end
        end else if (grant1) begin
            if (retire) begin
                prefer1 <= 1'b0;
                if (req0) begin
                    grant0 <= 1'b1;
                    grant1 <= 1'b0;
                end else if (req1) begin
                    grant0 <= 1'b0;
                    grant1 <= 1'b1;
                end else begin
                    grant0 <= 1'b0;
                    grant1 <= 1'b0;
                end
            end
        end else begin
            if (req0 && req1) begin
                grant0 <= !prefer1;
                grant1 <= prefer1;
            end else if (req0) begin
                grant0 <= 1'b1;
                grant1 <= 1'b0;
            end else if (req1) begin
                grant0 <= 1'b0;
                grant1 <= 1'b1;
            end else begin
                grant0 <= 1'b0;
                grant1 <= 1'b0;
            end
        end
    end

endmodule
