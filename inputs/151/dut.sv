module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    typedef enum logic [1:0] {
        IDLE,
        START,
        DATA,
        STOP
    } state_t;

    state_t state, next_state;
    logic [7:0] data_shift;
    logic [3:0] data_count;

    // State transitions
    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            data_shift <= 8'b0;
            data_count <= 4'd0;
        end else begin
            state <= next_state;
            case (next_state)
                DATA: begin
                    data_shift <= {in, data_shift[7:1]};
                    data_count <= data_count + 1;
                end
                default: begin
                    data_shift <= data_shift;
                    data_count <= 4'd0;
                end
            endcase
        end
    end

    // Next state logic
    always_comb begin
        next_state = state;  // Default to no state change
        done = 1'b0;  // Default done to 0

        case (state)
            IDLE: begin
                if (in == 1'b0) // start bit detected
                    next_state = START;
            end

            START: begin
                next_state = DATA;
            end

            DATA: begin
                if (data_count == 4'd7)
                    next_state = STOP;
                else
                    next_state = DATA;
            end

            STOP: begin
                if (in == 1'b1) begin // expected stop bit
                    next_state = IDLE;
                    out_byte = data_shift; // Capture the data byte
                    done = 1'b1; // Signal the data is valid
                end else begin
                    next_state = IDLE; // If stop bit not correct, reset to IDLE
                end
            end
        endcase
    end

endmodule
