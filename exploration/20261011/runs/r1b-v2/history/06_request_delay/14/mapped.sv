module gate(
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    localparam IDLE     = 2'b00;
    localparam ASSERT_Q = 2'b01;
    localparam COOLDOWN = 2'b10;

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            case (state)
                IDLE: begin
                    if (din)
                        state <= ASSERT_Q;
                    else
                        state <= IDLE;
                end
                ASSERT_Q: begin
                    state <= COOLDOWN;
                end
                COOLDOWN: begin
                    if (din)
                        state <= COOLDOWN;
                    else
                        state <= IDLE;
                end
                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

    assign q = (state == ASSERT_Q);

endmodule
