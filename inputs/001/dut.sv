module TopModule (
  input clk,
  input reset,
  input [2:0] s,
  output logic fr2,
  output logic fr1,
  output logic fr0,
  output logic dfr
);

  // State encoding: we need to track current water level based on sensors
  // and remember previous level to detect rising/falling
  
  typedef enum logic [2:0] {
    LEVEL_NONE  = 3'b000,  // Below s[0] - no sensors
    LEVEL_LOW   = 3'b001,  // Between s[1] and s[0] - only s[0]
    LEVEL_MID   = 3'b011,  // Between s[2] and s[1] - s[0], s[1]
    LEVEL_HIGH  = 3'b111   // Above s[2] - s[0], s[1], s[2]
  } level_t;
  
  level_t current_level, prev_level;
  logic rising;
  
  // Determine current level from sensors
  level_t sensor_level;
  always_comb begin
    case (s)
      3'b111: sensor_level = LEVEL_HIGH;
      3'b011: sensor_level = LEVEL_MID;
      3'b001: sensor_level = LEVEL_LOW;
      default: sensor_level = LEVEL_NONE;
    endcase
  end
  
  // Track previous level and rising condition
  always_ff @(posedge clk) begin
    if (reset) begin
      current_level <= LEVEL_NONE;
      prev_level <= LEVEL_NONE;
      rising <= 1'b0;
    end else begin
      // Update previous level when sensor state changes
      if (sensor_level != current_level) begin
        prev_level <= current_level;
        current_level <= sensor_level;
        // Rising if new level > previous level
        rising <= (sensor_level > current_level);
      end else begin
        rising <= 1'b0;  // No change, no rising
      end
    end
  end
  
  // Output logic based on current level and rising condition
  always_comb begin
    // Default: all off
    fr0 = 1'b0;
    fr1 = 1'b0;
    fr2 = 1'b0;
    dfr = 1'b0;
    
    if (reset) begin
      // Reset state: equivalent to low for long time
      fr0 = 1'b1;
      fr1 = 1'b1;
      fr2 = 1'b1;
      dfr = 1'b1;
    end else begin
      case (current_level)
        LEVEL_HIGH: begin
          // Above s[2]: no flow
          fr0 = 1'b0;
          fr1 = 1'b0;
          fr2 = 1'b0;
          dfr = 1'b0;
        end
        LEVEL_MID: begin
          // Between s[2] and s[1]: fr0
          fr0 = 1'b1;
          fr1 = 1'b0;
          fr2 = 1'b0;
          // Add supplemental if rising
          dfr = rising;
        end
        LEVEL_LOW: begin
          // Between s[1] and s[0]: fr0, fr1
          fr0 = 1'b1;
          fr1 = 1'b1;
          fr2 = 1'b0;
          // Add supplemental if rising
          dfr = rising;
        end
        LEVEL_NONE: begin
          // Below s[0]: maximum flow - fr0, fr1, fr2
          fr0 = 1'b1;
          fr1 = 1'b1;
          fr2 = 1'b1;
          // No supplemental needed (already max)
          dfr = 1'b0;
        end
        default: begin
          fr0 = 1'b1;
          fr1 = 1'b1;
          fr2 = 1'b1;
          dfr = 1'b1;
        end
      endcase
    end
  end

endmodule
