module TopModule (
    input logic clk,
    input logic in,
    input logic reset,
    output logic [7:0] out_byte,
    output logic done
);
    typedef enum logic [3:0] {
        IDLE,
        START,
        DATA,
        STOP
    } state_t;

    state_t state, next_state;
    logic [2:0] bit_count, next_bit_count;
    logic [7:0] shift_reg, next_shift_reg;
    logic next_done;

    // State register
    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            bit_count <= 0;
            shift_reg <= 0;
            done <= 0;
        end else begin
            state <= next_state;
            bit_count <= next_bit_count;
            shift_reg <= next_shift_reg;
            done <= next_done;
        end
    end

    // Next state logic
    always_comb begin
        next_state = state;
        next_bit_count = bit_count;
        next_shift_reg = shift_reg;
        next_done = 0;

        case (state)
            IDLE: begin
                if (in == 1'b0) begin
                    next_state = START;
                end
            end
            START: begin
                // Sample the first data bit
                next_shift_reg[0] = in;
                next_bit_count = 1;
                next_state = DATA;
            end
            DATA: begin
                next_shift_reg[bit_count] = in;
                if (bit_count == 7) begin
                    next_state = STOP;
                end else begin
                    next_bit_count = bit_count + 1;
                end
            end
            STOP: begin
                if (in == 1'b1) begin
                    next_done = 1;
                    next_state = IDLE;
                end else begin
                    // Stay in STOP until we see a 1
                    next_state = STOP;
                end
            end
        endcase
    end

    // Output assignments
    assign out_byte = (done) ? shift_reg : 8'b0;

endmodule
