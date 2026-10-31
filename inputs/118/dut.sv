module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [2:0]  s,
    output logic        fr2,
    output logic        fr1,
    output logic        fr0,
    output logic        dfr
);

    // Track previous sensor value to detect transitions
    logic [2:0] prev_s;

    // Descending level means the next 's' is lower than prev_s
    logic is_rising;

    // Combinational determination of nominal flow based on sensor
    logic [2:0] fr_nominal;

    always_comb begin
        case (s)
            3'b111 : fr_nominal = 3'b000;         // Above s[2]
            3'b011 : fr_nominal = 3'b001;         // Between s[2] and s[1]
            3'b001 : fr_nominal = 3'b011;         // Between s[1] and s[0]
            default: fr_nominal = 3'b111;         // Below s[0] (also resets here)
        endcase
    end

    // Is the current water level rising (fewer sensors asserted to more)?
    // That is, when the number of 1's in current sensor is greater than previous.
    // If so, supplemental flow is enabled (dfr=1).
    always_ff @(posedge clk) begin
        if (reset) begin
            prev_s <= 3'b000;
        end
        else begin
            prev_s <= s;
        end
    end

    // If more sensors are asserted now than in previous sample, level is rising
    assign is_rising = ($unsigned(s) > $unsigned(prev_s));

    // Outputs and state update
    always_ff @(posedge clk) begin
        if (reset) begin
            fr2 <= 1'b1;
            fr1 <= 1'b1;
            fr0 <= 1'b1;
            dfr <= 1'b1;
        end
        else begin
            fr2 <= fr_nominal[2];
            fr1 <= fr_nominal[1];
            fr0 <= fr_nominal[0];
            dfr <= is_rising;
        end
    end

endmodule
