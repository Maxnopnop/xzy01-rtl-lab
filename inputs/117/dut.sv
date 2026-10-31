module TopModule (
  input  logic       clk,
  input  logic       reset,
  input  logic [2:0] s,
  output logic       fr2,
  output logic       fr1,
  output logic       fr0,
  output logic       dfr
);

  // State encoding
  typedef enum logic [1:0] {
    LOW = 2'b00,
    BETWEEN_0_1 = 2'b01,
    BETWEEN_1_2 = 2'b10,
    HIGH = 2'b11
  } state_e;

  state_e current_state, next_state;
  logic   prev_level_above;

  // Synchronous state transitions with active-high synchronous reset
  always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
      current_state <= LOW;
      prev_level_above <= 1'b0;
    end else begin
      current_state <= next_state;
      // Track previous level's position relative to current level
      prev_level_above <= (s[2] || s[1]);
    end
  end

  // Combinational logic for next state and output generation
  always_comb begin
    // Default output values
    next_state = current_state;
    fr2 = 1'b0;
    fr1 = 1'b0;
    fr0 = 1'b0;
    dfr = 1'b0;

    unique case (s)
      3'b111: begin // Above s[2]
        next_state = HIGH;
        // All flow rates remain off
      end
      3'b011: begin // Between s[2] and s[1]
        next_state = BETWEEN_1_2;
        fr0 = 1'b1;
        dfr = (prev_level_above == 1'b0); // Increase flow if previous level was below
      end
      3'b001: begin // Between s[1] and s[0]
        next_state = BETWEEN_0_1;
        fr0 = 1'b1;
        fr1 = 1'b1;
        dfr = (prev_level_above == 1'b0); // Increase flow if previous level was below
      end
      3'b000: begin // Below s[0]
        next_state = LOW;
        fr0 = 1'b1;
        fr1 = 1'b1;
        fr2 = 1'b1;
        dfr = 1'b1; // Always suppliment flow below s[0]
      end
    endcase
  end

endmodule
