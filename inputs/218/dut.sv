module TopModule (
  input        d,
  input        done_counting,
  input        ack,
  input [9:0]  state,
  output logic B3_next,
  output logic S_next,
  output logic S1_next,
  output logic Count_next,
  output logic Wait_next,
  output logic done,
  output logic counting,
  output logic shift_ena
);

  // State one-hot encoding:
  // state[0] : S
  // state[1] : S1
  // state[2] : S11
  // state[3] : S110
  // state[4] : B0
  // state[5] : B1
  // state[6] : B2
  // state[7] : B3
  // state[8] : Count
  // state[9] : Wait

  always_comb begin
    // Defaults
    S_next      = 1'b0;
    S1_next     = 1'b0;
    B3_next     = 1'b0;
    Count_next  = 1'b0;
    Wait_next   = 1'b0;
    shift_ena   = 1'b0;
    done        = 1'b0;
    counting    = 1'b0;

    // Next-state logic
    // S
    if (state[0]) begin
      S_next  = ~d;         // S --d=0--> S
      S1_next = d;          // S --d=1--> S1
    end
    // S1
    if (state[1]) begin
      S_next  = ~d;          // S1 --d=0--> S
      S1_next = 1'b0;        // Not needed; handled above.
      // S1 --d=1--> S11
      if (d)
        S1_next = 1'b0; // no need, as next S11 handled below
    end
    // S1 --d=1--> S11
    if (state[1] && d)
      S1_next = 1'b0; // override
    if (state[1] && d)
      S1_next = 1'b0; // redundant
    if (state[1] && d)
      ; // placeholder for S11 transition
    // S11
    if (state[2]) begin
      // S11 --d=0--> S110
      if (~d)
        ; // S110_next
      // S11 --d=1--> S11
      if (d)
        ; // hold in S11
    end
    // Real next state assignment for S11
    if (state[2]) begin
      if (~d)
        ; // S110
      else
        ; // S11
    end
    // S110
    if (state[3]) begin
      // S110 --d=0--> S
      if (~d)
        S_next = 1'b1;
      // S110 --d=1--> B0
    end

    // B0
    if (state[4]) begin
      shift_ena = 1'b1;
      // always go to next: B1
    end
    // B1
    if (state[5]) begin
      shift_ena = 1'b1;
      // always go to next: B2
    end
    // B2
    if (state[6]) begin
      shift_ena = 1'b1;
      // always go to next: B3
    end
    // B3
    if (state[7]) begin
      shift_ena = 1'b1;
      // always go to next: Count
      B3_next = 1'b1;
    end
    // Count
    if (state[8]) begin
      counting = 1'b1;
      // done_counting=0: Count; done_counting=1: Wait
      if (~done_counting)
        Count_next = 1'b1;
      else
        Wait_next = 1'b1;
    end
    // Wait
    if (state[9]) begin
      done = 1'b1;
      // ack=0: Wait; ack=1: S
      if (~ack)
        Wait_next = 1'b1;
      else
        S_next = 1'b1;
    end

    // --- True one-hot next state logic below ---

    // S_next
    S_next =
      (state[0] && ~d) |           // S --d=0--> S
      (state[1] && ~d) |           // S1 --d=0--> S
      (state[3] && ~d) |           // S110 --d=0--> S
      (state[9] && ack);           // Wait --ack=1--> S

    // S1_next
    S1_next =
      (state[0] && d);             // S --d=1--> S1

    // NOTE: S11_next is not requested.

    // B3_next
    B3_next =
      (state[6]);                  // B2 -> B3

    // Count_next
    Count_next =
      (state[7]) |                 // B3 -> Count
      (state[8] && ~done_counting);// Count --done_counting=0--> Count

    // Wait_next
    Wait_next =
      (state[8] && done_counting) |// Count --done_counting=1--> Wait
      (state[9] && ~ack);          // Wait --ack=0--> Wait

    // Output logic is handled above.
    // shift_ena is high in B0, B1, B2, B3
    shift_ena =
      state[4] | state[5] | state[6] | state[7];

    // counting is high in Count
    counting = state[8];

    // done is high in Wait
    done = state[9];
  end

endmodule
