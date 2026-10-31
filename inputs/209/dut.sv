module TopModule (
  input  clk,
  input  areset,
  input  in,
  output logic out
);

  typedef enum logic {
    StateA, // Output 0
    StateB  // Output 1
  } state_e;

  state_e state_q, state_d;

  // Combinational next-state/output logic
  always_comb begin
    // Default assignments
    state_d = state_q;
    out = 1'b0;

    case (state_q)
      StateA: begin
        // Output for StateA
        out = 1'b0;
        // Transition logic
        if (in == 1'b0)
          state_d = StateB;
        else
          state_d = StateA;
      end
      StateB: begin
        // Output for StateB
        out = 1'b1;
        // Transition logic
        if (in == 1'b0)
          state_d = StateA;
        else
          state_d = StateB;
      end
      default: begin
        state_d = StateB;
        out = 1'b1;
      end
    endcase
  end

  // State register with asynchronous reset to StateB
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= StateB;
    end else begin
      state_q <= state_d;
    end
  end

endmodule
