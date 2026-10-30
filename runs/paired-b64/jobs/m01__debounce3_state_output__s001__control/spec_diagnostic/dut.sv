module debounce3(
    input  clk,
    input  rst_n,
    input  din,
    output reg q
);

    localparam [2:0] LOW_0  = 3'd0;
    localparam [2:0] LOW_1  = 3'd1;
    localparam [2:0] LOW_2  = 3'd2;
    localparam [2:0] HIGH_0 = 3'd3;
    localparam [2:0] HIGH_1 = 3'd4;

    reg [2:0] state;
    reg [2:0] next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= LOW_0;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            LOW_0: begin
                if (din)
                    next_state = LOW_1;
                else
                    next_state = LOW_0;
            end
            LOW_1: begin
                if (din)
                    next_state = LOW_2;
                else
                    next_state = LOW_0;
            end
            LOW_2: begin
                if (din)
                    next_state = HIGH_0;
                else
                    next_state = LOW_0;
            end
            HIGH_0: begin
                if (din)
                    next_state = HIGH_0;
                else
                    next_state = HIGH_1;
            end
            HIGH_1: begin
                if (din)
                    next_state = HIGH_0;
                else
                    next_state = LOW_0;
            end
            default: next_state = LOW_0;
        endcase
    end

    always @(*) begin
        case (state)
            HIGH_0: q = 1'b1;
            HIGH_1: q = 1'b1;
            default: q = 1'b0;
        endcase
    end

endmodule
