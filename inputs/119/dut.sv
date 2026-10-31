module TopModule (
  input        clk,
  input        reset,
  input  [2:0] s,
  output logic fr2,
  output logic fr1,
  output logic fr0,
  output logic dfr
);

  // State encoding: four levels
  typedef enum logic [1:0] {
    StBelowAllSensors,   // Below s[0] (lowest), none asserted; all flow on.
    StBetween0and1,      // Between s[1] and s[0], only s[0] asserted.
    StBetween1and2,      // Between s[2] and s[1], only s[0] and s[1] asserted.
    StAboveAllSensors    // Above s[2], all three asserted; zero flow.
  } water_level_e;

  // State for last transition direction
  typedef enum logic {
    DirUp,    // last change was to a higher water level
    DirDown   // last change was to a lower water level
  } dir_e;

  // State registers
  water_level_e  curr_level, next_level;
  dir_e          last_dir, next_last_dir;

  // Combinational output logic and next state logic
  always_comb begin
    // Defaults
    fr2 = 1'b0;
    fr1 = 1'b0;
    fr0 = 1'b0;
    dfr = 1'b0;
    next_level = curr_level;
    next_last_dir = last_dir;

    // Decode current inputs to next_level
    // s[2] = highest, s[0] = lowest
    if      (s == 3'b111)
      next_level = StAboveAllSensors;
    else if (s == 3'b011)
      next_level = StBetween1and2;
    else if (s == 3'b001)
      next_level = StBetween0and1;
    else // s == 3'b000
      next_level = StBelowAllSensors;

    // Determine direction: compare next_level and curr_level
    if (next_level > curr_level)
      next_last_dir = DirUp;
    else if (next_level < curr_level)
      next_last_dir = DirDown;
    else
      next_last_dir = last_dir;

    // Set outputs based on next_level and next_last_dir
    unique case (next_level)
      // Below all sensors: all assert
      StBelowAllSensors: begin
        fr2 = 1'b1;
        fr1 = 1'b1;
        fr0 = 1'b1;
        dfr = 1'b1;
      end

      // Between s[1] and s[0]: fr0, fr1, dfr for DirUp, only fr0+fr1 for DirDown
      StBetween0and1: begin
        fr0 = 1'b1;
        fr1 = 1'b1;
        dfr = (next_last_dir == DirUp);
      end

      // Between s[2] and s[1]: fr0, dfr for DirUp, only fr0 for DirDown
      StBetween1and2: begin
        fr0 = 1'b1;
        dfr = (next_last_dir == DirUp);
      end

      // Above all sensors: all off
      StAboveAllSensors: begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;
        dfr = 1'b0;
      end
      default: ;
    endcase
  end

  // State update; synchronous active-high reset
  always_ff @(posedge clk) begin
    if (reset) begin
      curr_level <= StBelowAllSensors;
      last_dir   <= DirDown;
    end else begin
      curr_level <= next_level;
      last_dir   <= next_last_dir;
    end
  end

endmodule
