module TopModule (
  input  clk,
  input  areset,
  input  x,
  output logic z
);

  // State encoding
  typedef enum logic [1:0] {
    IDLE,
    INVERT,
    PASS
  } state_e;

  state_e state_q, state_d;

  // Sequential state register with asynchronous reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= IDLE;
    end else begin
      state_q <= state_d;
    end
  end

  // Next state and output logic
  always_comb begin
    state_d = state_q;
    z = 1'b0;

    unique case (state_q)
      IDLE: begin
        if (x == 1'b1) begin
          state_d = INVERT;
          z = 1'b1;
        end else begin
          state_d = PASS;
          z = 1'b0;
        end
      end

      INVERT: begin
        state_d = INVERT;
        z = ~x;
      end

      PASS: begin
        state_d = PASS;
        z = x;
      end

      default: begin
        state_d = IDLE;
        z = 1'b0;
      end
    endcase
  end

endmodule
