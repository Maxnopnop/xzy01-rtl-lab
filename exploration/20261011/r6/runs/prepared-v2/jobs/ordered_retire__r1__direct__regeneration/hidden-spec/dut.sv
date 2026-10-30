module ordered_retire (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       flush,
    input  wire       issue,
    input  wire [1:0] issue_tag,
    input  wire       finish,
    input  wire [1:0] finish_tag,
    output reg  [1:0] count,
    output reg        retired,
    output reg  [1:0] retired_tag
);

    reg [1:0] tag0, tag1;
    reg       finished0, finished1;

    reg [1:0] next_count;
    reg [1:0] next_tag0, next_tag1;
    reg       next_finished0, next_finished1;
    reg       next_retired;
    reg [1:0] next_retired_tag;

    reg retire_old_head;
    reg accept_old_issue;

    always @* begin
        next_count        = count;
        next_tag0         = tag0;
        next_tag1         = tag1;
        next_finished0    = finished0;
        next_finished1    = finished1;
        next_retired      = 1'b0;
        next_retired_tag  = retired_tag;

        retire_old_head = (count != 2'b00) && finished0;

        accept_old_issue =
            issue &&
            (count < 2) &&
            !((count >= 1) && (issue_tag == tag0)) &&
            !((count >= 2) && (issue_tag == tag1));

        if (finish) begin
            if ((count >= 1) && (finish_tag == tag0))
                next_finished0 = 1'b1;
            if ((count >= 2) && (finish_tag == tag1))
                next_finished1 = 1'b1;
        end

        if (retire_old_head) begin
            next_retired     = 1'b1;
            next_retired_tag = tag0;

            if (count == 2) begin
                next_tag0      = tag1;
                next_finished0 = next_finished1;
                next_tag1      = 2'b00;
                next_finished1 = 1'b0;
                next_count     = 2'b01;
            end else begin
                next_tag0      = 2'b00;
                next_finished0 = 1'b0;
                next_tag1      = 2'b00;
                next_finished1 = 1'b0;
                next_count     = 2'b00;
            end
        end

        if (accept_old_issue) begin
            if (next_count == 0) begin
                next_tag0      = issue_tag;
                next_finished0 = 1'b0;
            end else begin
                next_tag1      = issue_tag;
                next_finished1 = 1'b0;
            end
            next_count = next_count + 1'b1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count       <= 2'b00;
            retired     <= 1'b0;
            retired_tag <= 2'b00;
            tag0        <= 2'b00;
            tag1        <= 2'b00;
            finished0   <= 1'b0;
            finished1   <= 1'b0;
        end else if (flush) begin
            count       <= 2'b00;
            retired     <= 1'b0;
            retired_tag <= 2'b00;
            tag0        <= 2'b00;
            tag1        <= 2'b00;
            finished0   <= 1'b0;
            finished1   <= 1'b0;
        end else begin
            count       <= next_count;
            retired     <= next_retired;
            retired_tag <= next_retired_tag;
            tag0        <= next_tag0;
            tag1        <= next_tag1;
            finished0   <= next_finished0;
            finished1   <= next_finished1;
        end
    end

endmodule
