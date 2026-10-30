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

    reg [3:0] den_reg;
    reg [3:0] num_work;
    reg [3:0] quot_work;
    reg [3:0] rem_work;
    reg [2:0] count;

    wire [4:0] trial;
    wire       subtract;
    wire [4:0] next_rem;
    wire [3:0] next_quot;

    assign trial     = {rem_work, num_work[3]};
    assign subtract  = (trial >= {1'b0, den_reg});
    assign next_rem  = subtract ? (trial - {1'b0, den_reg}) : trial;
    assign next_quot = {quot_work[2:0], subtract};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy      <= 1'b0;
            done      <= 1'b0;
            quotient  <= 4'b0000;
            remainder <= 4'b0000;
            den_reg   <= 4'b0000;
            num_work  <= 4'b0000;
            quot_work <= 4'b0000;
            rem_work  <= 4'b0000;
            count     <= 3'b000;
        end else if (abort) begin
            busy      <= 1'b0;
            done      <= 1'b0;
            quotient  <= 4'b0000;
            remainder <= 4'b0000;
            den_reg   <= 4'b0000;
            num_work  <= 4'b0000;
            quot_work <= 4'b0000;
            rem_work  <= 4'b0000;
            count     <= 3'b000;
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
                        busy      <= 1'b1;
                        den_reg   <= denominator;
                        num_work  <= numerator;
                        quot_work <= 4'b0000;
                        rem_work  <= 4'b0000;
                        count     <= 3'b000;
                    end
                end
            end else if (advance) begin
                num_work  <= {num_work[2:0], 1'b0};
                quot_work <= next_quot;
                rem_work  <= next_rem[3:0];

                if (count == 3) begin
                    busy      <= 1'b0;
                    done      <= 1'b1;
                    quotient  <= next_quot;
                    remainder <= next_rem[3:0];
                    count     <= 3'b000;
                end else begin
                    count <= count + 1'b1;
                end
            end
        end
    end

endmodule
