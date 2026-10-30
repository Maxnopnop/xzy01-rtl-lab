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

    reg        valid0, valid1;
    reg        done0, done1;
    reg [1:0]  tag0, tag1;

    reg        valid0_next, valid1_next;
    reg        done0_next, done1_next;
    reg [1:0]  tag0_next, tag1_next;
    reg [1:0]  count_next;
    reg        retired_next;
    reg [1:0]  retired_tag_next;

    reg        accept_issue;
    reg        retire_head;
    reg        old_done0, old_done1;

    always @* begin
        valid0_next     = valid0;
        valid1_next     = valid1;
        done0_next      = done0;
        done1_next      = done1;
        tag0_next       = tag0;
        tag1_next       = tag1;
        count_next      = count;
        retired_next    = 1'b0;
        retired_tag_next = retired_tag;

        retire_head = valid0 && done0;

        accept_issue = issue &&
                       (count < 2) &&
                       !(valid0 && (tag0 == issue_tag)) &&
                       !(valid1 && (tag1 == issue_tag));

        old_done0 = done0 || (finish && valid0 &&
                              (tag0 == finish_tag));
        old_done1 = done1 || (finish && valid1 &&
                              (tag1 == finish_tag));

        done0_next = old_done0;
        done1_next = old_done1;

        if (retire_head) begin
            retired_next     = 1'b1;
            retired_tag_next = tag0;

            valid0_next = valid1;
            tag0_next   = tag1;
            done0_next  = old_done1;

            valid1_next = 1'b0;
            tag1_next   = 2'b00;
            done1_next  = 1'b0;

            count_next = count - 1'b1;
        end

        if (accept_issue) begin
            if (retire_head) begin
                if (valid1) begin
                    valid1_next = 1'b1;
                    tag1_next   = issue_tag;
                    done1_next  = 1'b0;
                end else begin
                    valid0_next = 1'b1;
                    tag0_next   = issue_tag;
                    done0_next  = 1'b0;
                end
            end else if (!valid0) begin
                valid0_next = 1'b1;
                tag0_next   = issue_tag;
                done0_next  = 1'b0;
            end else begin
                valid1_next = 1'b1;
                tag1_next   = issue_tag;
                done1_next  = 1'b0;
            end

            count_next = count_next + 1'b1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid0      <= 1'b0;
            valid1      <= 1'b0;
            done0       <= 1'b0;
            done1       <= 1'b0;
            tag0        <= 2'b00;
            tag1        <= 2'b00;
            count       <= 2'b00;
            retired     <= 1'b0;
            retired_tag <= 2'b00;
        end else if (flush) begin
            valid0      <= 1'b0;
            valid1      <= 1'b0;
            done0       <= 1'b0;
            done1       <= 1'b0;
            tag0        <= 2'b00;
            tag1        <= 2'b00;
            count       <= 2'b00;
            retired     <= 1'b0;
            retired_tag <= 2'b00;
        end else begin
            valid0      <= valid0_next;
            valid1      <= valid1_next;
            done0       <= done0_next;
            done1       <= done1_next;
            tag0        <= tag0_next;
            tag1        <= tag1_next;
            count       <= count_next;
            retired     <= retired_next;
            retired_tag <= retired_tag_next;
        end
    end

endmodule
