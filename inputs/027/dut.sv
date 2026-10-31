module TopModule (
  input  clk,
  input  in,
  input  reset,
  output logic [7:0] out_byte,
  output logic done
);

  typedef enum logic [1:0] {
    IDLE  = 2'd0,
    DATA  = 2'd1,
    STOP  = 2'd2
  } state_e;

  state_e state;
  logic [2:0] bit_cnt;
  logic [7:0] shift_reg;

  always_ff @(posedge clk) begin
    if (reset) begin
      state     <= IDLE;
      bit_cnt   <= 3'd0;
      shift_reg <= 8'd0;
      out_byte  <= 8'd0;
      done      <= 1'b0;
    end else begin
      done <= 1'b0;

      case (state)
        IDLE: begin
          bit_cnt <= 3'd0;
          if (!in) begin
            state <= DATA;
          end
        end

        DATA: begin
          shift_reg <= {in, shift_reg[7:1]};
          if (bit_cnt == 3'd7) begin
            state <= STOP;
          end
          bit_cnt <= bit_cnt + 3'd1;
        end

        STOP: begin
          if (in) begin
            out_byte <= shift_reg;
            done     <= 1'b1;
            state    <= IDLE;
          end
        end

        default: begin
          state <= IDLE;
        end
      endcase
    end
  end

endmodule
