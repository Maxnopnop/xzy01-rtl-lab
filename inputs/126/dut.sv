module TopModule (
  input  logic clk,
  input  logic areset,
  input  logic x,
  output logic z
);

  typedef enum logic [1:0] {
    IDLE      = 2'b00,
    INVERT    = 2'b01,
    FORWARD   = 2'b10
  } state_e;

  state_e current_state, next_state;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= IDLE;
    end else begin
      current_state <= next_state;
    end
  end

  always_comb begin
    case (current_state)
      IDLE: begin
        if (x == 0) begin
          next_state = INVERT;
        end else begin
          next_state = FORWARD;
        end
      end
      INVERT: begin
        next_state = FORWARD;
      end
      FORWARD: begin
        next_state = FORWARD;
      end
      default: begin
        next_state = IDLE;
      end
    endcase
  end

  always_comb begin
    case (current_state)
      INVERT: z = ~x;
      FORWARD: z = x;
      default: z = 1'b0;
    endcase
  end

endmodule
