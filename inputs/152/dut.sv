module TopModule (
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);

    // State enumeration
    typedef enum logic[2:0] {
        Idle,         // Waiting for start bit
        Receiving,    // Receiving 8 data bits
        WaitStop,     // Waiting for stop bit
        Done          // Data byte received correctly
    } State_e;

    State_e current_state, next_state;
    logic [7:0] data_shift;
    logic [3:0] bit_count;

    // Combinational logic for state transition and output logic
    always_comb begin
        // Default assignments
        next_state = current_state;
        done = 1'b0;

        case (current_state)
            Idle: begin
                // Wait for the start bit (logic 0)
                if (in == 1'b0)
                    next_state = Receiving;
            end

            Receiving: begin
                // Shift in the data bits
                if (bit_count < 8) begin
                    next_state = Receiving;
                end else begin
                    next_state = WaitStop;
                end
            end

            WaitStop: begin
                // Expecting a stop bit (logic 1)
                if (in == 1'b1) begin
                    next_state = Done;
                end else begin
                    next_state = Idle; // Invalid stop bit, resync
                end
            end

            Done: begin
                // Successfully received a byte
                done = 1'b1;
                next_state = Idle;
            end

            default: begin
                next_state = Idle;
            end
        endcase
    end

    // Sequential logic for state and data shift register update
    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            current_state <= Idle;
            data_shift <= 8'b0;
            bit_count <= 4'b0;
        end else begin
            current_state <= next_state;

            case (current_state)
                Receiving: begin
                    data_shift <= {in, data_shift[7:1]}; // Shift in incoming data
                    bit_count <= bit_count + 1'b1;
                end
                Done: begin
                    out_byte <= data_shift;
                    bit_count <= 4'b0; // Reset bit counter
                end
                default: begin
                    bit_count <= 4'b0;
                end
            endcase
        end
    end

endmodule
