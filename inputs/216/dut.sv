module TopModule(
    input  logic       d,
    input  logic       done_counting,
    input  logic       ack,
    input  logic [9:0] state,
    output logic       B3_next,
    output logic       S_next,
    output logic       S1_next,
    output logic       Count_next,
    output logic       Wait_next,
    output logic       done,
    output logic       counting,
    output logic       shift_ena
);

    // Current state identifiers
    localparam logic [9:0] S      = 10'b0000000001;
    localparam logic [9:0] S1     = 10'b0000000010;
    localparam logic [9:0] S11    = 10'b0000000100;
    localparam logic [9:0] S110   = 10'b0000001000;
    localparam logic [9:0] B0     = 10'b0000010000;
    localparam logic [9:0] B1     = 10'b0000100000;
    localparam logic [9:0] B2     = 10'b0001000000;
    localparam logic [9:0] B3     = 10'b0010000000;
    localparam logic [9:0] Count  = 10'b0100000000;
    localparam logic [9:0] Wait   = 10'b1000000000;

    // Default assignments
    always_comb begin
        B3_next    = 1'b0;
        S_next     = 1'b0;
        S1_next    = 1'b0;
        Count_next = 1'b0;
        Wait_next  = 1'b0;
        done       = 1'b0;
        counting   = 1'b0;
        shift_ena  = 1'b0;

        case (state)
            // Initial State S
            S: begin
                if (d == 1'b0) begin
                    S_next = 1'b1; // Remain in S
                end else if (d == 1'b1) begin
                    S1_next = 1'b1; // Transition to S1
                end
            end

            // State S1
            S1: begin
                if (d == 1'b0) begin
                    S_next = 1'b1; // Transition back to S
                end else if (d == 1'b1) begin
                    S1_next = 1'b1; // Transition to S11
                end
            end

            // State S11
            S11: begin
                if (d == 1'b0) begin
                    S1_next = 1'b1; // Transition to S110
                end else if (d == 1'b1) begin
                    S1_next = 1'b1; // Remain in S11
                end
            end

            // State S110
            S110: begin
                if (d == 1'b0) begin
                    S_next = 1'b1; // Transition back to S
                end else if (d == 1'b1) begin
                    B3_next = 1'b1; // Transition to B0
                end
            end

            // State B0, directly transition to B1
            B0: begin
                B3_next = 1'b1;
                shift_ena = 1'b1;
            end

            // State B1, directly transition to B2
            B1: begin
                B3_next = 1'b1;
                shift_ena = 1'b1;
            end

            // State B2, directly transition to B3
            B2: begin
                B3_next = 1'b1;
                shift_ena = 1'b1;
            end

            // State B3, transition to Count
            B3: begin
                B3_next = 1'b1; // Transition to Count
                shift_ena = 1'b1;
            end

            // State Count
            Count: begin
                counting = 1'b1;
                if (done_counting == 1'b0) begin
                    Count_next = 1'b1; // Remain in Count
                end else if (done_counting == 1'b1) begin
                    Wait_next = 1'b1; // Transition to Wait
                end
            end

            // State Wait
            Wait: begin
                done = 1'b1;
                if (ack == 1'b0) begin
                    Wait_next = 1'b1; // Remain in Wait
                end else if (ack == 1'b1) begin
                    S_next = 1'b1; // Transition to S
                end
            end

            default: begin
                // Default to S to catch undefined states
                S_next = 1'b1;
            end
        endcase
    end
endmodule
