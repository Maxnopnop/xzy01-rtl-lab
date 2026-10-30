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

    reg [1:0] head_tag;
    reg [1:0] tail_tag;
    reg       head_finished;
    reg       tail_finished;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count         <= 2'd0;
            retired       <= 1'b0;
            retired_tag   <= 2'd0;
            head_tag      <= 2'd0;
            tail_tag      <= 2'd0;
            head_finished <= 1'b0;
            tail_finished <= 1'b0;
        end else if (flush) begin
            count         <= 2'd0;
            retired       <= 1'b0;
            retired_tag   <= 2'd0;
            head_tag      <= 2'd0;
            tail_tag      <= 2'd0;
            head_finished <= 1'b0;
            tail_finished <= 1'b0;
        end else begin
            retired <= 1'b0;

            case (count)
                2'd0: begin
                    head_finished <= 1'b0;
                    tail_finished <= 1'b0;

                    if (issue) begin
                        head_tag      <= issue_tag;
                        head_finished <= 1'b0;
                        count         <= 2'd1;
                    end
                end

                2'd1: begin
                    tail_finished <= 1'b0;

                    if (head_finished) begin
                        retired     <= 1'b1;
                        retired_tag <= head_tag;

                        if (issue && (issue_tag != head_tag)) begin
                            head_tag      <= issue_tag;
                            head_finished <= 1'b0;
                            count         <= 2'd1;
                        end else begin
                            head_finished <= 1'b0;
                            count         <= 2'd0;
                        end
                    end else begin
                        if (finish && (finish_tag == head_tag))
                            head_finished <= 1'b1;

                        if (issue && (issue_tag != head_tag)) begin
                            tail_tag      <= issue_tag;
                            tail_finished <= 1'b0;
                            count         <= 2'd2;
                        end
                    end
                end

                2'd2: begin
                    if (head_finished) begin
                        retired       <= 1'b1;
                        retired_tag   <= head_tag;
                        head_tag      <= tail_tag;
                        head_finished <= tail_finished |
                                         (finish && (finish_tag == tail_tag));
                        tail_finished <= 1'b0;
                        count         <= 2'd1;
                    end else begin
                        if (finish && (finish_tag == head_tag))
                            head_finished <= 1'b1;

                        if (finish && (finish_tag == tail_tag))
                            tail_finished <= 1'b1;
                    end
                end

                default: begin
                    count         <= 2'd0;
                    retired       <= 1'b0;
                    retired_tag   <= 2'd0;
                    head_tag      <= 2'd0;
                    tail_tag      <= 2'd0;
                    head_finished <= 1'b0;
                    tail_finished <= 1'b0;
                end
            endcase
        end
    end

endmodule
