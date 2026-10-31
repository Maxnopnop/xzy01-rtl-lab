module TopModule (
  input        clk,
  input        reset,
  input  [2:0] s,
  output logic fr2,
  output logic fr1,
  output logic fr0,
  output logic dfr
);

  // Water level encoding for states
  typedef enum logic [1:0] {
    BELOW_S0   = 2'b00,  // 0 sensors
    BETWEEN_S1 = 2'b01,  // only s[0] = 1
    BETWEEN_S2 = 2'b10,  // s[0]=1, s[1]=1, s[2]=0
    ABOVE_S2   = 2'b11   // all sensors 1
  } level_e;

  // Store the last stable water level for hysteresis
  logic [1:0] level_q, level_d;

  // Would the transition be up (from lower level) or not?
  logic transitioned_up_d;

  // Current computed water level from sensors
  level_e level_now;

  // 3'b111: ABOVE_S2
  // 3'b011: BETWEEN_S2_S1
  // 3'b001: BETWEEN_S1_S0
  // 3'b000: BELOW_S0
  always_comb begin
    unique case (s)
      3'b111: level_now = ABOVE_S2;
      3'b011: level_now = BETWEEN_S2;
      3'b001: level_now = BETWEEN_S1;
      default: level_now = BELOW_S0;
    endcase
  end

  // Level transition detection (for dfr logic)
  always_comb begin
    // Default: no transition up
    transitioned_up_d = 1'b0;
    // If level is increasing (current > previous), set the flag
    if (level_now > level_q)
      transitioned_up_d = 1'b1;
  end

  // Synchronous state update with synchronous active-high reset
  always_ff @(posedge clk) begin
    if (reset) begin
      // Water has been low for a long time, so go to lowest state
      level_q <= BELOW_S0;
    end else begin
      // Only update level on genuine sensor change
      // i.e., when s has changed from previous
      if (level_now != level_q)
        level_q <= level_now;
      else
        level_q <= level_q;
    end
  end

  // Output logic based on state and transition
  always_comb begin
    // Defaults
    fr0 = 1'b0; fr1 = 1'b0; fr2 = 1'b0; dfr = 1'b0;
    unique case (level_now)
      ABOVE_S2: begin
        // Above all sensors: flow off
        fr0 = 1'b0; fr1 = 1'b0; fr2 = 1'b0; dfr = 1'b0;
      end
      BETWEEN_S2: begin
        // Between s[2] and s[1]: fr0 nominal
        fr0 = 1'b1;
        fr1 = 1'b0;
        fr2 = 1'b0;
        // dfr high if we just transitioned up to this level
        dfr = (level_now > level_q) ? 1'b1 : 1'b0;
      end
      BETWEEN_S1: begin
        // Between s[1] and s[0]: fr0, fr1 nominal
        fr0 = 1'b1;
        fr1 = 1'b1;
        fr2 = 1'b0;
        dfr = (level_now > level_q) ? 1'b1 : 1'b0;
      end
      BELOW_S0: begin
        // Below s[0]: all flows high
        fr0 = 1'b1;
        fr1 = 1'b1;
        fr2 = 1'b1;
        dfr = 1'b1;
      end
      default: begin
        fr0 = 1'b0;
        fr1 = 1'b0;
        fr2 = 1'b0;
        dfr = 1'b0;
      end
    endcase
    // Reset overrides everything
    if (reset) begin
      fr0 = 1'b1;
      fr1 = 1'b1;
      fr2 = 1'b1;
      dfr = 1'b1;
    end
  end

endmodule
