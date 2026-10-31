module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    typedef enum logic [2:0] {
        IDLE,       // Waiting for start bit
        START,      // Detect start bit
        DATA,       // Receiving 8 data bits
        STOP_ERR,   // Wait for stop bit if missing
        DONE        // Stop bit received, byte valid
    } state_t;

    state_t state, next_state;

    logic [7:0]  data_reg, next_data_reg;
    logic [2:0]  bit_cnt, next_bit_cnt;
    logic        next_done;

    // FSM state and data registers
    always_ff @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            data_reg <= 8'b0;
            bit_cnt  <= 3'b0;
            done     <= 1'b0;
        end else begin
            state    <= next_state;
            data_reg <= next_data_reg;
            bit_cnt  <= next_bit_cnt;
            done     <= next_done;
        end
    end

    // Next state and output logic
    always_comb begin
        next_state    = state;
        next_data_reg = data_reg;
        next_bit_cnt  = bit_cnt;
        next_done     = 1'b0;
        out_byte      = data_reg;

        case (state)
            IDLE: begin
                if (in == 1'b0) begin // Detect start bit
                    next_state    = START;
                end
                next_data_reg = 8'b0;
                next_bit_cnt  = 3'b0;
            end

            START: begin
                // Stay in START only the first cycle after IDLE->START
                // ready to sample first data bit
                next_state    = DATA;
                next_bit_cnt  = 3'b0;
                next_data_reg = 8'b0;
            end

            DATA: begin
                next_data_reg = {in, data_reg[7:1]}; // LSB first
                if (bit_cnt == 3'd7) begin
                    next_state = (in == 1'b1) ? DONE : STOP_ERR; // in==stop bit?
                    // Note: After last data bit, in==stop bit
                end else begin
                    next_bit_cnt = bit_cnt + 3'd1;
                end
            end

            STOP_ERR: begin
                // Remain here until in==1 (stop bit detected)
                if (in == 1'b1) begin
                    next_state = IDLE;
                end
            end

            DONE: begin
                next_done = 1'b1;
                next_state = IDLE;
            end

            default: begin
                next_state = IDLE;
            end
        endcase
    end

endmodule
