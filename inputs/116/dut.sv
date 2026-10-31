module TopModule (
  input        clk,
  input        reset,
  input  [2:0] s,
  output logic fr2,
  output logic fr1,
  output logic fr0,
  output logic dfr
);

  typedef enum logic [1:0] {
    Low = 2'b00,
    Mid = 2'b01,
    High = 2'b10,
    Above = 2'b11
  } water_level_t;

  water_level_t state, next_state;
  logic         prev_low;

  // State register
  always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
      state <= Low;
      prev_low <= 1;
    end else begin
      state <= next_state;
      if (state == Low)
        prev_low <= 1;
      else if (state == Above)
        prev_low <= 0;
    end
  end

  // Combinational logic for next state and outputs
  always_comb begin
    // Default assignments
    next_state = state;
    fr2 = 0;
    fr1 = 0;
    fr0 = 0;
    dfr = 0;

    case (state)
      Low: begin
        // Below s[0], All valves open
        fr2 = 1;
        fr1 = 1;
        fr0 = 1;
        dfr = 1;
        if (s == 3'b111) next_state = Above;
        else if (s == 3'b110) next_state = High;
        else if (s == 3'b100) next_state = Mid;
      end
      Mid: begin
        // Between s[1] and s[0], Nominal: fr0, fr1
        fr1 = 1;
        fr0 = 1;
        if (prev_low) dfr = 1;
        
        if (s == 3'b111) next_state = Above;
        else if (s == 3'b110) next_state = High;
      end
      High: begin
        // Between s[2] and s[1], Nominal: fr0
        fr0 = 1;
        if (prev_low) dfr = 1;
        
        if (s == 3'b111) next_state = Above;
        else if (s == 3'b000) next_state = Low;
      end
      Above: begin
        // Above s[2], all valves closed
        if (s == 3'b000) next_state = Low;
      end
    endcase
  end

endmodule
