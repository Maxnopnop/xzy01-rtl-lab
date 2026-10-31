module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic in,
  output logic out
);

  typedef enum logic {
    STATE_A,
    STATE_B
  } state_e;

  state_e state_q, state_d;

  always_comb begin
    unique case (state_q)
      STATE_A: begin
        if (in) begin
          state_d = STATE_A;
        end else begin
          state_d = STATE_B;
        end
      end
      STATE_B: begin
        if (in) begin
          state_d = STATE_B;
        end else begin
          state_d = STATE_A;
        end
      end
      default: begin
        state_d = STATE_B;
      end
    endcase
  end

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= STATE_B;
    end else begin
      state_q <= state_d;
    end
  end

  assign out = (state_q == STATE_B);

endmodule
