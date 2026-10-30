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

    reg [1:0] tag0;
    reg [1:0] tag1;
    reg       done0;
    reg       done1;

    wire retire_old =
        (count != 2'd0) && done0;

    wire issue_accept =
        issue &&
        (count < 2'd2) &&
        !((count >= 2'd1) && (issue_tag == tag0)) &&
        !((count == 2'd2) && (issue_tag == tag1));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count       <= 2'd0;
            retired     <= 1'b0;
            retired_tag <= 2'd0;
            tag0        <= 2'd0;
            tag1        <= 2'd0;
            done0       <= 1'b0;
            done1       <= 1'b0;
        end else if (flush) begin
            count       <= 2'd0;
            retired     <= 1'b0;
            retired_tag <= 2'd0;
            tag0        <= 2'd0;
            tag1        <= 2'd0;
            done0       <= 1'b0;
            done1       <= 1'b0;
        end else begin
            retired <= retire_old;

            if (retire_old)
                retired_tag <= tag0;

            case (count)
                2'd0: begin
                    if (issue_accept) begin
                        count <= 2'd1;
                        tag0  <= issue_tag;
                        done0 <= 1'b0;
                    end
                end

                2'd1: begin
                    if (retire_old) begin
                        if (issue_accept) begin
                            count <= 2'd1;
                            tag0  <= issue_tag;
                            done0 <= 1'b0;
                        end else begin
                            count <= 2'd0;
                            tag0  <= 2'd0;
                            done0 <= 1'b0;
                        end
                    end else begin
                        if (finish && (finish_tag == tag0))
                            done0 <= 1'b1;

                        if (issue_accept) begin
                            count <= 2'd2;
                            tag1  <= issue_tag;
                            done1 <= 1'b0;
                        end
                    end
                end

                2'd2: begin
                    if (retire_old) begin
                        count <= 2'd1;
                        tag0  <= tag1;
                        done0 <= done1 ||
                                 (finish && (finish_tag == tag1));
                        tag1  <= 2'd0;
                        done1 <= 1'b0;
                    end else begin
                        if (finish && (finish_tag == tag0))
                            done0 <= 1'b1;

                        if (finish && (finish_tag == tag1))
                            done1 <= 1'b1;
                    end
                end

                default: begin
                    count <= 2'd0;
                    tag0  <= 2'd0;
                    tag1  <= 2'd0;
                    done0 <= 1'b0;
                    done1 <= 1'b0;
                end
            endcase
        end
    end

endmodule
