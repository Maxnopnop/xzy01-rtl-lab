module TopModule (
  input        clk,
  input        in,
  input        reset,
  output logic [7:0] out_byte,
  output logic       done
);

  typedef enum logic [2:0] {
    IDLE        = 3'd0,
    START       = 3'd1,
    DATA        = 3'd2,
    STOP        = 3'd3,
    ERROR_WAIT  = 3'd4
  } state_e;

  state_e state_q, state_d;
  logic [7:0] shift_reg_q, shift_reg_d;
  logic [2:0] bit_cnt_q, bit_cnt_d;
  logic [7:0] out_byte_d;
  logic       done_d;

  // Next-state logic
  always_comb begin
    state_d     = state_q;
    shift_reg_d = shift_reg_q;
    bit_cnt_d   = bit_cnt_q;
    out_byte_d  = out_byte; // hold value unless we assign in STOP
    done_d      = 1'b0;

    unique case (state_q)
      IDLE: begin
        if (in == 1'b0) begin // Detect start bit
          state_d     = START;
        end
      end
      START: begin
        // Sample start bit for one cycle, move to data bit collection
        // Implicitly assume proper sampling, no oversampling.
        state_d     = DATA;
        bit_cnt_d   = 3'd0;
        shift_reg_d = 8'd0;
      end
      DATA: begin
        shift_reg_d = {in, shift_reg_q[7:1]}; // Shift in LSB first (incoming 'in' at MSB, but we count bits up)
        if (bit_cnt_q == 3'd7) begin
          state_d   = STOP;
        end else begin
          bit_cnt_d = bit_cnt_q + 3'd1;
        end
      end
      STOP: begin
        if (in == 1'b1) begin
          out_byte_d = shift_reg_d; // Correctly received byte
          done_d     = 1'b1;
          state_d    = IDLE;
        end else begin
          // If stop bit not detected, wait for line to go high (idle)
          state_d = ERROR_WAIT;
        end
      end
      ERROR_WAIT: begin
        // Wait for line to go high (idle) before looking for next byte
        if (in == 1'b1) begin
          state_d = IDLE;
        end
      end
      default: begin
        state_d     = IDLE;
        shift_reg_d = 8'd0;
        bit_cnt_d   = 3'd0;
        out_byte_d  = 8'd0;
        done_d      = 1'b0;
      end
    endcase
  end

  // Sequential logic
  always_ff @(posedge clk) begin
    if (reset) begin
      state_q     <= IDLE;
      shift_reg_q <= 8'd0;
      bit_cnt_q   <= 3'd0;
      out_byte    <= 8'd0;
      done        <= 1'b0;
    end else begin
      state_q     <= state_d;
      shift_reg_q <= shift_reg_d;
      bit_cnt_q   <= bit_cnt_d;
      out_byte    <= out_byte_d;
      done        <= done_d;
    end
  end

endmodule
