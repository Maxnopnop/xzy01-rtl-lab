module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    typedef enum logic [1:0] {
        LOW,     // Below s[0]
        MID_LOW, // Between s[1] and s[0]
        MID_HIGH,// Between s[2] and s[1]
        HIGH     // Above s[2]
    } water_level_t;

    water_level_t current_state, previous_state;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            // Reset state to LOW (below s[0]) with bonus flow opened
            current_state <= LOW;
            previous_state <= LOW;
        end else begin
            previous_state <= current_state;
            case (s)
                3'b111: current_state <= HIGH;      // Above s[2]
                3'b011: current_state <= MID_HIGH;  // Between s[2] and s[1]
                3'b001: current_state <= MID_LOW;   // Between s[1] and s[0]
                default: current_state <= LOW;      // Below s[0]
            endcase
        end
    end

    always_comb begin
        // Default outputs
        fr2 = 0;
        fr1 = 0;
        fr0 = 0;
        dfr = 0;

        case (current_state)
            HIGH: begin
                // No flow
                fr2 = 0;
                fr1 = 0;
                fr0 = 0;
                dfr = 0;
            end
            MID_HIGH: begin
                // Nominal flow fr0
                fr2 = 0;
                fr1 = 0;
                fr0 = 1;
                dfr = (previous_state == MID_LOW || previous_state == LOW) ? 1 : 0;
            end
            MID_LOW: begin
                // Nominal flow fr0, fr1
                fr2 = 0;
                fr1 = 1;
                fr0 = 1;
                dfr = (previous_state == LOW) ? 1 : 0;
            end
            LOW: begin
                // Max flow fr0, fr1, fr2
                fr2 = 1;
                fr1 = 1;
                fr0 = 1;
                dfr = 1;
            end
        endcase
    end

endmodule
