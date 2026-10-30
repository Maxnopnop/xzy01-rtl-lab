module sequence_detector (
    input  wire clk,
    input  wire rst_n,
    input  wire data_in,
    output reg  sequence_detected
);

    localparam [2:0] IDLE = 3'd0;
    localparam [2:0] S1   = 3'd1;
    localparam [2:0] S2   = 3'd2;
    localparam [2:0] S3   = 3'd3;
    localparam [2:0] S4   = 3'd4;

    reg [2:0] state;
    reg [2:0] next_state;

    always @(*) begin
        next_state = IDLE;
        case (state)
            IDLE: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = IDLE;
            end

            S1: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = S2;
            end

            S2: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = S3;
            end

            S3: begin
                if (data_in)
                    next_state = S4;
                else
                    next_state = IDLE;
            end

            S4: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = S2;
            end

            default: next_state = IDLE;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        if (state == S4)
            sequence_detected = 1'b1;
        else
            sequence_detected = 1'b0;
    end

endmodule
