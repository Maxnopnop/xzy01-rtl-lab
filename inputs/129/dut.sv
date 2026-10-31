module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  // State: 0 if we're before the first 1, 1 if we've passed the first 1
  typedef enum logic {
    BEFORE_ONE = 1'b0,
    AFTER_ONE  = 1'b1
  } state_e;

  state_e state_q, state_d;
  logic z_d;

  // Next state and output logic
  always_comb begin
    state_d = state_q;
    z_d = 1'b0;
    unique case (state_q)
      BEFORE_ONE: begin
        if (x == 1'b1) begin
          state_d = AFTER_ONE;
          z_d = 1'b1; // 2's complement: invert + add 1
        end else begin
          z_d = 1'b0; // invert
        end
      end
      AFTER_ONE: begin
        state_d = AFTER_ONE;
        z_d = x; // pass through
      end
      default: begin
        state_d = BEFORE_ONE;
        z_d = 1'b0;
      end
    endcase
  end

  // State register and async reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= BEFORE_ONE;
      z <= 1'b0;
    end else begin
      state_q <= state_d;
      z <= z_d;
    end
  end

endmodule
