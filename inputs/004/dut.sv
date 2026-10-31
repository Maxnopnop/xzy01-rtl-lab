module TopModule (
    input logic clk,
    input logic reset,
    input logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);
    typedef enum logic [1:0] {
        LEVEL_BELOW_S0,
        LEVEL_BETWEEN_S1_S0,
        LEVEL_BETWEEN_S2_S1,
        LEVEL_ABOVE_S2
    } state_t;

    state_t current_state, next_state;
    logic prev_level_lower;

    // State transition - combinational
    always_comb begin
        case (s)
            3'b000: next_state = LEVEL_BELOW_S0;
            3'b001: next_state = LEVEL_BETWEEN_S1_S0;
            3'b011: next_state = LEVEL_BETWEEN_S2_S1;
            3'b111: next_state = LEVEL_ABOVE_S2;
            default: next_state = current_state;
        endcase
    end

    // prev_level_lower detection - combinational
    always_comb begin
        case ({current_state, next_state})
            {LEVEL_BELOW_S0, LEVEL_BETWEEN_S1_S0},
            {LEVEL_BELOW_S0, LEVEL_BETWEEN_S2_S1},
            {LEVEL_BELOW_S0, LEVEL_ABOVE_S2},
            {LEVEL_BETWEEN_S1_S0, LEVEL_BETWEEN_S2_S1},
            {LEVEL_BETWEEN_S1_S0, LEVEL_ABOVE_S2},
            {LEVEL_BETWEEN_S2_S1, LEVEL_ABOVE_S2}: prev_level_lower = 1'b1;
            default: prev_level_lower = 1'b0;
        endcase
    end

    // State register - sequential
    always_ff @(posedge clk) begin
        if (reset) begin
            current_state <= LEVEL_BELOW_S0;
        end else begin
            current_state <= next_state;
        end
    end

    // Output logic - combinational
    always_comb begin
        if (reset) begin
            fr2 = 1'b1;
            fr1 = 1'b1;
            fr0 = 1'b1;
            dfr = 1'b1;
        end else begin
            case (current_state)
                LEVEL_BELOW_S0: begin
                    fr2 = 1'b1;
                    fr1 = 1'b1;
                    fr0 = 1'b1;
                    dfr = 1'b1;
                end
                LEVEL_BETWEEN_S1_S0: begin
                    fr2 = 1'b0;
                    fr1 = 1'b1;
                    fr0 = 1'b1;
                    dfr = prev_level_lower;
                end
                LEVEL_BETWEEN_S2_S1: begin
                    fr2 = 1'b0;
                    fr1 = 1'b0;
                    fr0 = 1'b1;
                    dfr = prev_level_lower;
                end
                LEVEL_ABOVE_S2: begin
                    fr2 = 1'b0;
                    fr1 = 1'b0;
                    fr0 = 1'b0;
                    dfr = 1'b0;
                end
                default: begin
                    fr2 = 1'b0;
                    fr1 = 1'b0;
                    fr0 = 1'b0;
                    dfr = 1'b0;
                end
            endcase
        end
    end
endmodule
