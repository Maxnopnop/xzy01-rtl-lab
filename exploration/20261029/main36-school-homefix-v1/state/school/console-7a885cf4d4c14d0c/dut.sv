module TopModule (
  input              clk,
  input              load,
  input      [511:0] data,
  output logic [511:0] q
);

  logic [511:0] next_state;

  always_comb begin
    for (int i = 0; i < 512; i++) begin
      logic left, center, right;
      // boundary conditions: out of range neighbors are zero
      left   = (i == 511) ? 1'b0 : q[i + 1];
      center = q[i];
      right  = (i == 0) ? 1'b0 : q[i - 1];

      // Apply Rule 110:
      // next_state[i] = (left, center, right) mapping:
      // 111 -> 0
      // 110 -> 1
      // 101 -> 1
      // 100 -> 0
      // 011 -> 1
      // 010 -> 1
      // 001 -> 1
      // 000 -> 0
      // Truth table for next_state[i]:
      // next = (~left & center & ~right) | (left & center & ~right) | (left & ~center & right) | (~left & center & right) | (~left & ~center & right);

      // Simplify per table:
      //
      // next_state[i] = 
      //   (left & center & ~right) +  // 110
      //   (left & ~center & right) +  // 101
      //   (~left & center & right) +  // 011
      //   (~left & center & ~right) + // 010
      //   (~left & ~center & right);  // 001

      next_state[i] = (left & center & ~right) |
                      (left & ~center & right) |
                      (~left & center & right) |
                      (~left & center & ~right) |
                      (~left & ~center & right);
    end
  end

  always_ff @(posedge clk) begin
    if (load) begin
      q <= data;
    end else begin
      q <= next_state;
    end
  end

endmodule
