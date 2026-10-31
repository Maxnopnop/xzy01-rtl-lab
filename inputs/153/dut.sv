module TopModule (
  input        clk,
  input        in,
  input        reset,
  output logic [7:0] out_byte,
  output logic       done
);

  typedef enum logic [2:0] {
    IDLE,
    START,
    DATA,
    STOP
  } fsm_state_e;

  fsm_state_e state, next_state;
  logic [2:0] bit_count;
  logic [7:0] byte_buffer;

  always_ff @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      bit_count <= 3'd0;
      byte_buffer <= 8'b0;
      done <= 1'b0;
    end else begin
      state <= next_state;
      if (state == DATA) begin
        byte_buffer <= {in, byte_buffer[7:1]};
        bit_count <= bit_count + 1;
      end
      if (state == STOP && in) begin
        out_byte <= byte_buffer;
      end
      if (state == STOP) begin
        done <= in;
      end else begin
        done <= 1'b0;
      end
    end
  end

  always_comb begin
    next_state = state;
    unique case (state)
      IDLE: begin
        if (!in) begin
          next_state = START;
        end
      end
      START: begin
        if (in) begin
          next_state = IDLE;
        end else begin
          next_state = DATA;
          bit_count = 3'd0;
        end
      end
      DATA: begin
        if (bit_count == 3'd7) begin
          next_state = STOP;
        end
      end
      STOP: begin
        if (in) begin
          next_state = IDLE;
        end else begin
          next_state = IDLE;
        end
      end
      default: next_state = IDLE;
    endcase
  end

endmodule
