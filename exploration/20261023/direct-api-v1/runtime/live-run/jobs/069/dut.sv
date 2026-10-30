module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    typedef enum logic [1:0] {
        IDLE,
        RECEIVE,
        STOP_CHECK,
        WAIT_STOP
    } state_t;

    state_t state, next_state;
    logic [7:0] shift_reg;
    logic [2:0] bit_count;

    always_comb begin
        next_state = state;

        case (state)
            IDLE: begin
                if (!in)
                    next_state = RECEIVE;
            end

            RECEIVE: begin
                if (bit_count == 3'd7)
                    next_state = STOP_CHECK;
            end

            STOP_CHECK: begin
                if (in)
                    next_state = IDLE;
                else
                    next_state = WAIT_STOP;
            end

            WAIT_STOP: begin
                if (in)
                    next_state = IDLE;
            end

            default: begin
                next_state = IDLE;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset)
            state <= IDLE;
        else
            state <= next_state;
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            shift_reg <= 8'b0;
            bit_count <= 3'b0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;

            if ((state == IDLE) && !in) begin
                shift_reg <= 8'b0;
                bit_count <= 3'b0;
            end else if (state == RECEIVE) begin
                shift_reg <= {in, shift_reg[7:1]};

                if (bit_count != 3'd7)
                    bit_count <= bit_count + 3'd1;
            end

            if ((state == STOP_CHECK) && in)
                done <= 1'b1;
        end
    end

    assign out_byte = shift_reg;

endmodule
