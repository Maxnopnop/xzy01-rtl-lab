module TopModule (
  input  clk,
  input  areset,
  input  bump_left,
  input  bump_right,
  output logic walk_left,
  output logic walk_right
);

  typedef enum logic {
    WalkLeft  = 1'b0,
    WalkRight = 1'b1
  } state_t;

  state_t state_q, state_d;

  // Combinational next-state decode
  always_comb begin
    state_d = state_q;

    case (state_q)
      // Walking left: bump on either side (or both) switches to the right
      WalkLeft: begin
        if (bump_left || bump_right) begin
          state_d = WalkRight;
        end
      end

      // Walking right: bump on either side (or both) switches to the left
      WalkRight: begin
        if (bump_left || bump_right) begin
          state_d = WalkLeft;
        end
      end

      default: begin
        state_d = WalkLeft;
      end
    endcase
  end

  // State register with asynchronous positive-edge reset to WalkLeft
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= WalkLeft;
    end else begin
      state_q <= state_d;
    end
  end

  // Moore outputs
  assign walk_left  = (state_q == WalkLeft);
  assign walk_right = (state_q == WalkRight);

endmodule
