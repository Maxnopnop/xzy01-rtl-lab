module TopModule(
    input  logic        d,
    input  logic        done_counting,
    input  logic        ack,
    input  logic [9:0]  state,
    output logic        B3_next,
    output logic        S_next,
    output logic        S1_next,
    output logic        Count_next,
    output logic        Wait_next,
    output logic        done,
    output logic        counting,
    output logic        shift_ena
);

    // State bits (one-hot assignment for clarity)
    logic S      = state[0];
    logic S1     = state[1];
    logic S11    = state[2];
    logic S110   = state[3];
    logic B0     = state[4];
    logic B1     = state[5];
    logic B2     = state[6];
    logic B3     = state[7];
    logic Count  = state[8];
    logic Wait   = state[9];

    // Next-state logic (one-hot)
    // S_next: Next state will be S
    assign S_next =
        (S      && (~d))           || // S  + d=0 -> S
        (S1     && (~d))           || // S1 + d=0 -> S
        (S110   && (~d))           || // S110 + d=0 -> S
        (Wait   && ack)            ;  // Wait + ack=1 -> S

    // S1_next: Next state will be S1
    assign S1_next =
        (S      && d)              ; // S + d=1 -> S1

    // S11_next: Next state will be S11 (not required in outputs)

    // Count_next: Next state will be Count
    assign Count_next =
        (B3     )                   || // B3 always go to Count
        (Count  && ~done_counting ) ; // Count, done_counting=0 -> stay at Count

    // Wait_next: Next state will be Wait
    assign Wait_next =
        (Count  && done_counting)   || // Count, done_counting=1 -> Wait
        (Wait   && ~ack)            ; // Wait, ack=0 -> Wait
    
    // B3_next: Next state will be B3
    assign B3_next =
        (B2     )                   ; // B2 always go to B3

    // S1_next: In this encoding, note that S1_next only comes from S and d=1.
    // But in S1, d=1 -> S11, so S1_next already handled.
    // However, from provided outputs, only next S1 requested.

    // Output Logic
    assign shift_ena =
        B0 | B1 | B2 | B3;

    assign counting =
        Count;

    assign done =
        Wait;

endmodule
