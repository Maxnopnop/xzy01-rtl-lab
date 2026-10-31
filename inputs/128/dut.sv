module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  // Moore FSM with two states:
  // BEFORE_ONE: haven't seen first '1' yet, so just copy inputs
  // AFTER_ONE: have seen the first '1', output is inverted input
  typedef enum logic [0:0] {
    BEFORE_ONE = 1'b0,
    AFTER_ONE  = 1'b1
  } state_e;

  state_e state_q, state_d;

  // Output logic
  always_comb begin
    unique case (state_q)
      BEFORE_ONE: z = x;
      AFTER_ONE:  z = ~x;
      default:    z = 1'b0;
    endcase
  end

  // State transition
  always_comb begin
    unique case (state_q)
      BEFORE_ONE: state_d = (x == 1'b1) ? AFTER_ONE : BEFORE_ONE;
      AFTER_ONE : state_d = AFTER_ONE;
      default:    state_d = BEFORE_ONE;
    endcase
  end

  // State register with async active-high reset
  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      state_q <= BEFORE_ONE;
    end else begin
      state_q <= state_d;
    end
  end

endmodule
