module TopModule (
  input             clk,
  input             load,
  input      [511:0] data,
  output logic [511:0] q
);

  logic [511:0] state;
  logic [511:0] next_state;

  // Compute next state combinationally based on Rule 110
  always_comb begin
    for (int i = 0; i < 512; i++) begin
      logic left, center, right;
      left   = (i == 511) ? 1'b0 : state[i+1];
      center = state[i];
      right  = (i == 0)   ? 1'b0 : state[i-1];

      // Map (left, center, right) to next center state by Rule 110 truth table:
      // Rule 110 for 3-bit neighborhood: 111=0,110=1,101=1,100=0,011=1,010=1,001=1,000=0
      // The 8-bit rule number for Rule 110 is binary: 01101110 (from bit 7 to 0)
      // Index = {left,center,right}
      // next_state = rule110[ {left,center,right} ];
      case ({left, center, right})
        3'b111: next_state[i] = 1'b0;
        3'b110: next_state[i] = 1'b1;
        3'b101: next_state[i] = 1'b1;
        3'b100: next_state[i] = 1'b0;
        3'b011: next_state[i] = 1'b1;
        3'b010: next_state[i] = 1'b1;
        3'b001: next_state[i] = 1'b1;
        3'b000: next_state[i] = 1'b0;
        default: next_state[i] = 1'b0; // safe default
      endcase
    end
  end

  // Sequential logic for state update and load
  always_ff @(posedge clk) begin
    if (load) begin
      state <= data;
    end else begin
      state <= next_state;
    end
  end

  assign q = state;

endmodule
