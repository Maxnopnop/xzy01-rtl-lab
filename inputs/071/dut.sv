module TopModule (
  input              d,
  input              done_counting,
  input              ack,
  input [9:0]        state,
  output logic       B3_next,
  output logic       S_next,
  output logic       S1_next,
  output logic       Count_next,
  output logic       Wait_next,
  output logic       done,
  output logic       counting,
  output logic       shift_ena
);

  // One-hot state encoding:
  // S      = 10'b0000000001
  // S1     = 10'b0000000010
  // S11    = 10'b0000000100
  // S110   = 10'b0000001000
  // B0     = 10'b0000010000
  // B1     = 10'b0000100000
  // B2     = 10'b0001000000
  // B3     = 10'b0010000000
  // Count  = 10'b0100000000
  // Wait   = 10'b1000000000

  always_comb begin
    // Default next-state signals are zero
    B3_next    = 1'b0;
    S_next     = 1'b0;
    S1_next    = 1'b0;
    Count_next = 1'b0;
    Wait_next  = 1'b0;

    // Default outputs
    done     = 1'b0;
    counting = 1'b0;
    shift_ena = 1'b0;

    case (state)
      10'b0000000001: begin // S
        if (d) begin
          S1_next = 1'b1;
        end else begin
          S_next = 1'b1;
        end
      end

      10'b0000000010: begin // S1
        if (d) begin
          S1_next = 1'b1;
        end else begin
          S_next = 1'b1;
        end
      end

      10'b0000000100: begin // S11
        if (d) begin
          S1_next = 1'b1;
        end else begin
          S_next = 1'b1;
        end
      end

      10'b0000001000: begin // S110
        if (d) begin
          B3_next = 1'b1;
        end else begin
          S_next = 1'b1;
        end
      end

      10'b0000010000: begin // B0
        shift_ena = 1'b1;
        // next state B1 (not exposed as an output)
      end

      10'b0000100000: begin // B1
        shift_ena = 1'b1;
      end

      10'b0001000000: begin // B2
        shift_ena = 1'b1;
      end

      10'b0010000000: begin // B3
        shift_ena = 1'b1;
        Count_next = 1'b1;
      end

      10'b0100000000: begin // Count
        counting = 1'b1;
        if (done_counting) begin
          Wait_next = 1'b1;
        end else begin
          Count_next = 1'b1;
        end
      end

      10'b1000000000: begin // Wait
        done = 1'b1;
        if (ack) begin
          S_next = 1'b1;
        end else begin
          Wait_next = 1'b1;
        end
      end

      default: begin
        S_next = 1'b1;
      end
    endcase
  end

endmodule
