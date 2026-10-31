module TopModule (
  input              d,
  input              done_counting,
  input              ack,
  input       [9:0]  state,
  output logic       B3_next,
  output logic       S_next,
  output logic       S1_next,
  output logic       Count_next,
  output logic       Wait_next,
  output logic       done,
  output logic       counting,
  output logic       shift_ena
);

  always_comb begin
    // Default values for next state signals
    B3_next    = 1'b0;
    S_next     = 1'b0;
    S1_next    = 1'b0;
    Count_next = 1'b0;
    Wait_next  = 1'b0;
    
    // Default values for output logic
    done       = 1'b0;
    counting   = 1'b0;
    shift_ena  = 1'b0;
    
    // Determine next state and outputs based on current state and inputs
    case (state)
      // S State: initial state
      10'b0000000001: begin
        if (d == 1'b0) S_next = 1'b1;
        else           S1_next = 1'b1;
      end
      
      // S1 State
      10'b0000000010: begin
        if (d == 1'b0) S_next = 1'b1;
        else           state = 10'b0000000100; // Transition to S11
      end
      
      // S11 State
      10'b0000000100: begin
        if (d == 1'b0) state = 10'b0000001000; // Transition to S110
        else           state = 10'b0000000100; // Remain in S11
      end
      
      // S110 State
      10'b0000001000: begin
        if (d == 1'b0) S_next = 1'b1;
        else           state = 10'b0000010000; // Transition to B0
      end
      
      // B0 State
      10'b0000010000: begin
        shift_ena = 1'b1;
        state = 10'b0000100000; // Transition to B1
      end
      
      // B1 State
      10'b0000100000: begin
        shift_ena = 1'b1;
        state = 10'b0001000000; // Transition to B2
      end
      
      // B2 State
      10'b0001000000: begin
        shift_ena = 1'b1;
        state = 10'b0010000000; // Transition to B3
      end
      
      // B3 State
      10'b0010000000: begin
        shift_ena = 1'b1;
        B3_next = 1'b1;
        state = 10'b0100000000; // Transition to Count
      end
      
      // Count State
      10'b0100000000: begin
        counting = 1'b1;
        if (done_counting == 1'b0) state = 10'b0100000000; // Remain in Count
        else                      state = 10'b1000000000; // Transition to Wait
      end

      // Wait State
      10'b1000000000: begin
        done = 1'b1;
        if (ack == 1'b0) Wait_next = 1'b1;
        else            S_next = 1'b1;
      end
      
      default: begin
        S_next = 1'b1; // Default to S state
      end
    endcase
  end

endmodule
