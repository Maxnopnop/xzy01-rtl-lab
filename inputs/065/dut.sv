module TopModule (
  input  clk,
  input  areset,
  input  in,
  output logic out
);

  typedef enum logic {
    A,
    B
  } state_e;

  state_e state_d, state_q;

  always_comb begin
    state_d = state_q;
    out = 1'b0;

    case (state_q)
      A: begin
        out = 1'b0;
        if (in) begin
          state_d = A;
        end else begin
          state_d = B;
        end
      end
      B: begin
        out = 1'b1;
        if (in) begin
          state_d = B;
        end else begin
          state_d = A;
        end
      end
      default: begin
        state_d = B;
      end
    endcase
  end

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= B;
    end else begin
      state_q <= state_d;
    end
  end

endmodule
