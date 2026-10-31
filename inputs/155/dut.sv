module TopModule (
  input        clk,
  input        in,
  input        reset,
  output logic [7:0] out_byte,
  output logic       done
);

  typedef enum logic [2:0] {
    Idle,        // Waiting for start bit (line is idle, high)
    Start,       // Start bit detected (should be 0)
    Data,        // Receiving 8 data bits (LSB first)
    Stop,        // Waiting for stop bit (should be 1)
    Fail         // Invalid stop bit; wait for line to return to 1
  } State_e;

  State_e        state_q, state_d;
  logic  [7:0]   byte_q, byte_d;
  logic  [2:0]   bitcnt_q, bitcnt_d;
  logic          done_d;

  // Combinational logic for FSM
  always_comb begin
    // Defaults
    state_d   = state_q;
    byte_d    = byte_q;
    bitcnt_d  = bitcnt_q;
    out_byte  = byte_q;
    done_d    = 1'b0;

    unique case (state_q)
      Idle: begin
        // Waiting for start bit (0)
        if (in == 1'b0) begin
          state_d = Start;
        end
      end

      Start: begin
        // Latch start bit (which we already know is zero), begin data collection
        state_d   = Data;
        bitcnt_d  = 3'd0;
        byte_d    = 8'b0;
      end

      Data: begin
        // Shift in 8 bits LSB first
        byte_d[bitcnt_q] = in;
        if (bitcnt_q == 3'd7)
          state_d  = Stop;       // Collected 8 data bits, now get stop bit
        else
          bitcnt_d = bitcnt_q + 3'd1;
      end

      Stop: begin
        if (in == 1'b1) begin
          // Valid stop bit
          done_d   = 1'b1;
          state_d  = Idle;
        end else begin
          // Invalid stop bit; wait for line to go high before next byte
          state_d = Fail;
        end
      end

      Fail: begin
        // Wait for line to return to idle (high) before attempting to resync
        if (in == 1'b1)
          state_d = Idle;
      end

      default: begin
        state_d = Idle;
      end
    endcase
  end

  // Sequential logic
  always_ff @(posedge clk) begin
    if (reset) begin
      state_q   <= Idle;
      byte_q    <= '0;
      bitcnt_q  <= '0;
      done      <= 1'b0;
    end else begin
      state_q   <= state_d;
      byte_q    <= byte_d;
      bitcnt_q  <= bitcnt_d;
      done      <= done_d;
    end
  end

endmodule
