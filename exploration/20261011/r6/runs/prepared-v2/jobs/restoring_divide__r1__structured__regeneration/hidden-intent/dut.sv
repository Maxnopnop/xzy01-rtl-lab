module restoring_divide (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       abort,
    input  wire       start,
    input  wire       advance,
    input  wire [3:0] numerator,
    input  wire [3:0] denominator,
    output reg        busy,
    output reg        done,
    output reg  [3:0] quotient,
    output reg  [3:0] remainder
);

    reg [3:0] divisor_r;
    reg [3:0] dividend_r;
    reg [4:0] partial_r;
    reg [3:0] quotient_work_r;
    reg [1:0] count_r;

    wire [4:0] trial_w;
    wire       subtract_w;
    wire [4:0] partial_next_w;
    wire [3:0] quotient_next_w;

    assign trial_w = {partial_r[3:0], dividend_r[3]};
    assign subtract_w = (trial_w >= {1'b0, divisor_r});
    assign partial_next_w = subtract_w
                          ? trial_w - {1'b0, divisor_r}
                          : trial_w;
    assign quotient_next_w = {quotient_work_r[2:0], subtract_w};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy            <= 1'b0;
            done            <= 1'b0;
            quotient        <= 4'b0000;
            remainder       <= 4'b0000;
            divisor_r       <= 4'b0000;
            dividend_r      <= 4'b0000;
            partial_r       <= 5'b00000;
            quotient_work_r <= 4'b0000;
            count_r         <= 2'b00;
        end else if (abort) begin
            busy            <= 1'b0;
            done            <= 1'b0;
            quotient        <= 4'b0000;
            remainder       <= 4'b0000;
            divisor_r       <= 4'b0000;
            dividend_r      <= 4'b0000;
            partial_r       <= 5'b00000;
            quotient_work_r <= 4'b0000;
            count_r         <= 2'b00;
        end else begin
            done <= 1'b0;

            if (busy) begin
                if (advance) begin
                    dividend_r      <= {dividend_r[2:0], 1'b0};
                    partial_r       <= partial_next_w;
                    quotient_work_r <= quotient_next_w;

                    if (count_r == 2'd3) begin
                        busy      <= 1'b0;
                        done      <= 1'b1;
                        quotient  <= quotient_next_w;
                        remainder <= partial_next_w[3:0];
                        count_r   <= 2'b00;
                    end else begin
                        count_r <= count_r + 2'd1;
                    end
                end
            end else if (start) begin
                divisor_r       <= denominator;
                dividend_r      <= numerator;
                partial_r       <= 5'b00000;
                quotient_work_r <= 4'b0000;
                count_r         <= 2'b00;

                if (denominator == 4'b0000) begin
                    busy      <= 1'b0;
                    done      <= 1'b1;
                    quotient  <= 4'b1111;
                    remainder <= numerator;
                end else begin
                    busy <= 1'b1;
                end
            end
        end
    end

endmodule
