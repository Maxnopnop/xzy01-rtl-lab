module request_delay (
    input  clk,
    input  rst_n,
    input  din,
    output reg q
);

    localparam [1:0] IDLE     = 2'b00;
    localparam [1:0] DELAY    = 2'b01;
    localparam [1:0] PULSE    = 2'b10;
    localparam [1:0] COOLDOWN = 2'b11;

    reg [1:0] state;
    reg [1:0] next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (din)
                    next_state = DELAY;
                else
                    next_state = IDLE;
            end
            DELAY: begin
                next_state = PULSE;
            end
            PULSE: begin
                next_state = COOLDOWN;
            end
            COOLDOWN: begin
                if (din)
                    next_state = COOLDOWN;
                else
                    next_state = IDLE;
            end
            default: begin
                next_state = IDLE;
            end
        endcase
    end

    always @(*) begin
        case (state)
            PULSE:   q = 1'b1;
            default: q = 1'b0;
        endcase
    end

endmodule
