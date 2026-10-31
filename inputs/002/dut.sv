module TopModule (
  input        clk,
  input        reset,
  input  [2:0] s,
  output       fr2,
  output       fr1,
  output       fr0,
  output       dfr
);

  // Level encodings, ordered from lowest to highest water level
  localparam logic [1:0] LEVEL_BELOW_0    = 2'd0;
  localparam logic [1:0] LEVEL_BETWEEN_01 = 2'd1;
  localparam logic [1:0] LEVEL_BETWEEN_12 = 2'd2;
  localparam logic [1:0] LEVEL_ABOVE_2    = 2'd3;

  logic [1:0] level_q, level_d;

  logic [2:0] pattern;

  always_comb begin
    if (s[2]) begin
      pattern = 3'b111;
    end else if (s[1]) begin
      pattern = 3'b011;
    end else if (s[0]) begin
      pattern = 3'b001;
    end else begin
      pattern = 3'b000;
    end
  end

  // Decode sensor pattern into a water level
  logic [1:0] current_level;
  always_comb begin
    unique case (pattern)
      3'b111:  current_level = LEVEL_ABOVE_2;
      3'b011:  current_level = LEVEL_BETWEEN_12;
      3'b001:  current_level = LEVEL_BETWEEN_01;
      default: current_level = LEVEL_BELOW_0;
    endcase
  end

  // State register: holds the previous water level
  always_ff @(posedge clk) begin
    if (reset) begin
      level_q <= LEVEL_BELOW_0;
    end else begin
      level_q <= level_d;
    end
  end

  // Combinational next-state and output logic
  always_comb begin
    level_d = current_level;

    // Defaults: no flow (above highest sensor)
    fr2 = 1'b0;
    fr1 = 1'b0;
    fr0 = 1'b0;
    dfr = 1'b0;

    unique case (current_level)
      // Below lowest sensor: maximum flow
      LEVEL_BELOW_0: begin
        fr2 = 1'b1;
        fr1 = 1'b1;
        fr0 = 1'b1;
      end

      // Between s[1] and s[0]: nominal fr0, fr1
      LEVEL_BETWEEN_01: begin
        fr2 = 1'b0;
        fr1 = 1'b1;
        fr0 = 1'b1;
        // Previous level lower -> increase flow
        if (level_q < current_level) begin
          dfr = 1'b1;
        end
      end

      // Between s[2] and s[1]: nominal fr0
      LEVEL_BETWEEN_12: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b1;
        // Previous level lower -> increase flow
        if (level_q < current_level) begin
          dfr = 1'b1;
        end
      end

      // Above highest sensor: no flow
      LEVEL_ABOVE_2: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;
      end
    endcase
  end

endmodule
