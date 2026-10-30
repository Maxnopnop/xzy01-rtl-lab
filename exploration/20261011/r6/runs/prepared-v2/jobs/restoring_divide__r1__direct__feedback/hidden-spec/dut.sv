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

    reg [3:0] numerator_work;
    reg [3:0] denominator_work;
    reg [3:0] quotient_work;
    reg [3:0] remainder_work;
    reg [2:0] advance_count;

    reg [4:0] trial_remainder;
    reg [4:0] next_remainder;
    reg [3:0] next_quotient;

    always @* begin
        trial_remainder = {remainder_work, numerator_work[3]};

        if (trial_remainder >= {1'b0, denominator_work}) begin
            next_remainder = trial_remainder - {1'b0, denominator_work};
            next_quotient  = {quotient_work[2:0], 1'b1};
        end else begin
            next_remainder = trial_remainder;
            next_quotient  = {quotient_work[2:0], 1'b0};
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy             <= 1'b0;
            done             <= 1'b0;
            quotient         <= 4'b0000;
            remainder        <= 4'b0000;
            numerator_work   <= 4'b0000;
            denominator_work <= 4'b0000;
            quotient_work    <= 4'b0000;
            remainder_work   <= 4'b0000;
            advance_count    <= 3'b000;
        end else if (abort) begin
            busy             <= 1'b0;
            done             <= 1'b0;
            quotient         <= 4'b0000;
            remainder        <= 4'b0000;
            numerator_work   <= 4'b0000;
            denominator_work <= 4'b0000;
            quotient_work    <= 4'b0000;
            remainder_work   <= 4'b0000;
            advance_count    <= 3'b000;
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
                        busy             <= 1'b1;
                        numerator_work   <= numerator;
                        denominator_work <= denominator;
                        quotient_work    <= 4'b0000;
                        remainder_work   <= 4'b0000;
                        advance_count    <= 3'b000;
                    end
                end
            end else if (advance) begin
                numerator_work <= {numerator_work[2:0], 1'b0};
                quotient_work  <= next_quotient;
                remainder_work <= next_remainder[3:0];

                if (advance_count == 3'd3) begin
                    busy          <= 1'b0;
                    done          <= 1'b1;
                    quotient      <= next_quotient;
                    remainder     <= next_remainder[3:0];
                    advance_count <= 3'b000;
                end else begin
                    advance_count <= advance_count + 3'd1;
                end
            end
        end
    end

endmodule
