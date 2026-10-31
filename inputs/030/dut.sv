module TopModule (
    input         clk,
    input         in,
    input         reset,
    output [7:0]  out_byte,
    output        done
);

    typedef enum logic [3:0] {
        IDLE,
        START,
        DATA,
        STOP,
        WAIT_STOP
    } state_e;

    state_e state_d, state_q;
    logic [2:0] bit_count_d, bit_count_q;
    logic [7:0] shift_reg_d, shift_reg_q;
    logic done_d, done_q;

    // Next state logic
    always_comb begin
        state_d = state_q;
        bit_count_d = bit_count_q;
        shift_reg_d = shift_reg_q;
        done_d = 1'b0;

        unique case (state_q)
            IDLE: begin
                if (in == 1'b0) begin
                    state_d = START;
                end
            end

            START: begin
                state_d = DATA;
                bit_count_d = 3'd0;
            end

            DATA: begin
                shift_reg_d = {in, shift_reg_q[7:1]}; // LSB first
                if (bit_count_q == 3'd7) begin
                    state_d = STOP;
                end else begin
                    bit_count_d = bit_count_q + 1'b1;
                end
            end

            STOP: begin
                if (in == 1'b1) begin
                    state_d = IDLE;
                    done_d = 1'b1;
                end else begin
                    state_d = WAIT_STOP;
                end
            end

            WAIT_STOP: begin
                if (in == 1'b1) begin
                    state_d = IDLE;
                end
            end

            default: begin
                state_d = IDLE;
                bit_count_d = 3'd0;
                shift_reg_d = 8'h00;
            end
        endcase
    end

    // Sequential logic
    always_ff @(posedge clk) begin
        if (reset) begin
            state_q    <= IDLE;
            bit_count_q <= 3'd0;
            shift_reg_q <= 8'h00;
            done_q     <= 1'b0;
        end else begin
            state_q    <= state_d;
            bit_count_q <= bit_count_d;
            shift_reg_q <= shift_reg_d;
            done_q     <= done_d;
        end
    end

    assign out_byte = shift_reg_q;
    assign done = done_q;

endmodule
