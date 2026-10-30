module request_delay (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    localparam [1:0] IDLE     = 2'b00;
    localparam [1:0] ASSERT_Q = 2'b01;
    localparam [1:0] COOLDOWN = 2'b10;

    reg [1:0] state;
    reg [1:0] next_state;

    always @(*) begin
        case (state)
            IDLE: begin
                if (din)
                    next_state = ASSERT_Q;
                else
                    next_state = IDLE;
            end

            ASSERT_Q: begin
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

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    assign q = (state == ASSERT_Q);

endmodule
