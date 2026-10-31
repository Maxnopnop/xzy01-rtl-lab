module TopModule (
  input  logic       clk,
  input  logic       in,
  input  logic       reset,
  output logic [7:0] out_byte,
  output logic       done
);

  typedef enum logic [3:0] {
    StIdle,
    StData0,
    StData1,
    StData2,
    StData3,
    StData4,
    StData5,
    StData6,
    StData7,
    StStop
  } state_e;

  state_e state_q, state_d;
  logic [7:0] data_q, data_d;

  always_comb begin
    state_d = state_q;
    data_d  = data_q;
    done    = 1'b0;

    unique case (state_q)
      StIdle: begin
        if (!in) state_d = StData0;
      end

      StData0: begin
        data_d[0] = in;
        state_d   = StData1;
      end

      StData1: begin
        data_d[1] = in;
        state_d   = StData2;
      end

      StData2: begin
        data_d[2] = in;
        state_d   = StData3;
      end

      StData3: begin
        data_d[3] = in;
        state_d   = StData4;
      end

      StData4: begin
        data_d[4] = in;
        state_d   = StData5;
      end

      StData5: begin
        data_d[5] = in;
        state_d   = StData6;
      end

      StData6: begin
        data_d[6] = in;
        state_d   = StData7;
      end

      StData7: begin
        data_d[7] = in;
        state_d   = StStop;
      end

      StStop: begin
        if (in) begin
          done    = 1'b1;
          state_d = StIdle;
        end
      end

      default: state_d = StIdle;
    endcase
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      state_q   <= StIdle;
      data_q    <= 8'h00;
      out_byte  <= 8'h00;
    end else begin
      state_q <= state_d;
      data_q  <= data_d;
      if (done) out_byte <= data_q;
    end
  end

endmodule
