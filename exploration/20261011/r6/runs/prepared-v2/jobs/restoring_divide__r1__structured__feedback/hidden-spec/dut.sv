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

    wire [4:0] trial;
    wire       trial_ge_divisor;
    wire [4:0] partial_next;
    wire [3:0] quotient_next;

    assign trial = {partial_r[3:0], dividend_r[3]};
    assign trial_ge_divisor = (trial >= {1'b0, divisor_r});
    assign partial_next = trial_ge_divisor
                        ? trial - {1'b0, divisor_r}
                        : trial;
    assign quotient_next = {quotient_work_r[2:0], trial_ge_divisor};

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

            if (!busy) begin
                if (start) begin
                    if (denominator == 4'b0000) begin
                        busy      <= 1'b0;
                        done      <= 1'b1;
                        quotient  <= 4'b1111;
                        remainder <= numerator;
                    end else begin
                        busy            <= 1'b1;
                        divisor_r       <= denominator;
                        dividend_r      <= numerator;
                        partial_r       <= 5'b00000;
                        quotient_work_r <= 4'b0000;
                        count_r         <= 2'b00;
                    end
                end
            end else if (advance) begin
                dividend_r      <= {dividend_r[2:0], 1'b0};
                partial_r       <= partial_next;
                quotient_work_r <= quotient_next;

                if (count_r == 2'd3) begin
                    busy      <= 1'b0;
                    done      <= 1'b1;
                    quotient  <= quotient_next;
                    remainder <= partial_next[3:0];
                    count_r   <= 2'b00;
                end else begin
                    count_r <= count_r + 2'd1;
                end
            end
        end
    end

endmodule
