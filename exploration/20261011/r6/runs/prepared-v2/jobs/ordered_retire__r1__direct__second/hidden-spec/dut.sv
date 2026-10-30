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

    reg       valid0, valid1;
    reg       finished0, finished1;
    reg [1:0] tag0, tag1;

    reg       next_valid0, next_valid1;
    reg       next_finished0, next_finished1;
    reg [1:0] next_tag0, next_tag1;
    reg [1:0] next_count;
    reg       next_retired;
    reg [1:0] next_retired_tag;

    reg accept_issue;
    reg retire_head;

    always @* begin
        next_valid0       = valid0;
        next_valid1       = valid1;
        next_finished0    = finished0;
        next_finished1    = finished1;
        next_tag0         = tag0;
        next_tag1         = tag1;
        next_count        = count;
        next_retired      = 1'b0;
        next_retired_tag  = retired_tag;

        retire_head = valid0 && finished0;

        accept_issue = issue &&
                       (count < 2) &&
                       !(valid0 && (tag0 == issue_tag)) &&
                       !(valid1 && (tag1 == issue_tag));

        if (finish && valid0 && (finish_tag == tag0))
            next_finished0 = 1'b1;

        if (finish && valid1 && (finish_tag == tag1))
            next_finished1 = 1'b1;

        if (retire_head) begin
            next_retired     = 1'b1;
            next_retired_tag = tag0;

            next_valid0      = valid1;
            next_tag0        = tag1;
            next_finished0   = next_finished1;

            next_valid1      = 1'b0;
            next_tag1        = 2'b00;
            next_finished1   = 1'b0;

            next_count       = count - 1'b1;
        end

        if (accept_issue) begin
            if (retire_head || !valid0) begin
                next_valid0     = 1'b1;
                next_tag0       = issue_tag;
                next_finished0  = 1'b0;
            end else begin
                next_valid1     = 1'b1;
                next_tag1       = issue_tag;
                next_finished1  = 1'b0;
            end

            next_count = next_count + 1'b1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid0       <= 1'b0;
            valid1       <= 1'b0;
            finished0    <= 1'b0;
            finished1    <= 1'b0;
            tag0         <= 2'b00;
            tag1         <= 2'b00;
            count        <= 2'b00;
            retired      <= 1'b0;
            retired_tag  <= 2'b00;
        end else if (flush) begin
            valid0       <= 1'b0;
            valid1       <= 1'b0;
            finished0    <= 1'b0;
            finished1    <= 1'b0;
            tag0         <= 2'b00;
            tag1         <= 2'b00;
            count        <= 2'b00;
            retired      <= 1'b0;
            retired_tag  <= 2'b00;
        end else begin
            valid0       <= next_valid0;
            valid1       <= next_valid1;
            finished0    <= next_finished0;
            finished1    <= next_finished1;
            tag0         <= next_tag0;
            tag1         <= next_tag1;
            count        <= next_count;
            retired      <= next_retired;
            retired_tag  <= next_retired_tag;
        end
    end

endmodule
