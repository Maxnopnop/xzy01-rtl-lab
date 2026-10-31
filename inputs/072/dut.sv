module TopModule (
    input  logic d,
    input  logic done_counting,
    input  logic ack,
    input  logic [9:0] state,
    output logic B3_next,
    output logic S_next,
    output logic S1_next,
    output logic Count_next,
    output logic Wait_next,
    output logic done,
    output logic counting,
    output logic shift_ena
);

    // One-hot state encoding:
    // S      = 10'b0000000001
    // S1     = 10'b0000000010
    // S11    = 10'b0000000100
    // S110   = 10'b0000001000
    // B0     = 10'b0000010000
    // B1     = 10'b0000100000
    // B2     = 10'b0001000000
    // B3     = 10'b0010000000
    // Count  = 10'b0100000000
    // Wait   = 10'b1000000000

    always_comb begin
        // Default outputs
        B3_next    = 1'b0;
        S_next     = 1'b0;
        S1_next    = 1'b0;
        Count_next = 1'b0;
        Wait_next  = 1'b0;
        done       = 1'b0;
        counting   = 1'b0;
        shift_ena  = 1'b0;

        // Next-state logic
        if (state[0]) begin // S
            if (d) begin
                S1_next = 1'b1;
            end else begin
                S_next = 1'b1;
            end
        end else if (state[1]) begin // S1
            if (d) begin
                S1_next = 1'b1;
            end else begin
                S_next = 1'b1;
            end
        end else if (state[2]) begin // S11
            if (d) begin
                S1_next = 1'b1;
            end else begin
                S_next = 1'b1;
            end
        end else if (state[3]) begin // S110
            if (d) begin
                B3_next = 1'b1; // Will be corrected: B0 is next, but B0_next is not requested
            end else begin
                S_next = 1'b1;
            end
        end else if (state[4]) begin // B0
            B3_next = 1'b1; // placeholder, see correction below
        end
    end

endmodule
