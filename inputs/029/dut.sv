module TopModule (
    input  logic        clk,
    input  logic        in,
    input  logic        reset,
    output logic [7:0]  out_byte,
    output logic        done
);
    // State encoding
    typedef enum logic [1:0] {
        Idle,
        Data,
        WaitStop
    } state_e;

    state_e state_q, state_d;
    logic [2:0] bit_cnt_q, bit_cnt_d;
    logic [7:0] shift_reg_q, shift_reg_d;
    logic done_d;

    // Combinational decode
    always_comb begin
        state_d = state_q;
        bit_cnt_d = bit_cnt_q;
        shift_reg_d = shift_reg_q;
        done_d = 1'b0;

        unique case (state_q)
            Idle: begin
                if (in == 1'b0) begin
                    state_d = Data;
                    bit_cnt_d = 3'd0;
                    shift_reg_d = 8'h00;
                end
            end

            Data: begin
                shift_reg_d = {in, shift_reg_q[7:1]};
                if (bit_cnt_q == 3'd7) begin
                    state_d = WaitStop;
                end else begin
                    bit_cnt_d = bit_cnt_q + 3'd1;
                end
            end

            WaitStop: begin
                if (in == 1'b1) begin
                    done_d = 1'b1;
                    state_d = Idle;
                end
            end

            default: begin
                state_d = Idle;
            end
        endcase
    end

    // Sequential logic
    always_ff @(posedge clk) begin
        if (reset) begin
            state_q <= Idle;
            bit_cnt_q <= 3'd0;
            shift_reg_q <= 8'h00;
            out_byte <= 8'h00;
            done <= 1'b0;
        end else begin
            state_q <= state_d;
            bit_cnt_q <= bit_cnt_d;
            shift_reg_q <= shift_reg_d;
            out_byte <= shift_reg_d;
            done <= done_d;
        end
    end
endmodule
