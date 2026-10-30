module sticky_alarm (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    reg [1:0] state;
    reg [1:0] next_state;

    localparam S0 = 2'b00;
    localparam S1 = 2'b01;
    localparam S2 = 2'b10;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            S0: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S0;
            end
            S1: begin
                if (din)
                    next_state = S2;
                else
                    next_state = S0;
            end
            S2: next_state = S2;
            default: next_state = S0;
        endcase
    end

    assign q = (state == S2);

endmodule
