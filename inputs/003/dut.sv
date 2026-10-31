module TopModule (
  input  logic       clk,
  input  logic       reset,
  input  logic [2:0] s,
  output logic       fr2,
  output logic       fr1,
  output logic       fr0,
  output logic       dfr
);

  // Water level states, ordered from lowest to highest
  typedef enum logic [1:0] {
    LEVEL_BELOW = 2'd0,
    LEVEL_BETWEEN_LOW_HIGH = 2'd1,  // between s[1] and s[0]
    LEVEL_BETWEEN_HIGH_TOP = 2'd2,  // between s[2] and s[1]
    LEVEL_ABOVE = 2'd3
  } level_e;

  level_e level_q, level_d;
  logic   lower_prev_q, lower_prev_d;

  // Determine current level from sensors
  always_comb begin
    if (!s[0]) begin
      level_d = LEVEL_BELOW;
    end else if (!s[1]) begin
      level_d = LEVEL_BETWEEN_LOW_HIGH;
    end else if (!s[2]) begin
      level_d = LEVEL_BETWEEN_HIGH_TOP;
    end else begin
      level_d = LEVEL_ABOVE;
    end
  end

  // Determine whether previous level was lower than current level
  always_comb begin
    lower_prev_d = lower_prev_q;
    if (level_d != level_q) begin
      lower_prev_d = (level_q < level_d);
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      level_q      <= LEVEL_BELOW;
      lower_prev_q <= 1'b0;
    end else begin
      level_q      <= level_d;
      lower_prev_q <= lower_prev_d;
    end
  end

  // Flow rate outputs
  always_comb begin
    fr2 = 1'b0;
    fr1 = 1'b0;
    fr0 = 1'b0;
    dfr = 1'b0;

    case (level_q)
      LEVEL_BELOW: begin
        fr2 = 1'b1;
        fr1 = 1'b1;
        fr0 = 1'b1;
      end
      LEVEL_BETWEEN_LOW_HIGH: begin
        fr1 = 1'b1;
        fr0 = 1'b1;
        dfr = lower_prev_q;
      end
      LEVEL_BETWEEN_HIGH_TOP: begin
        fr0 = 1'b1;
        dfr = lower_prev_q;
      end
      LEVEL_ABOVE: begin
        // no nominal flow
      end
      default: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;
        dfr = 1'b0;
      end
    endcase
  end

endmodule
