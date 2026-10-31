module TopModule (
    input        clk,
    input        in,
    input        reset,
    output logic [7:0] out_byte,
    output logic       done
);

    typedef enum logic [1:0] {
        IDLE,
        DATA,
        STOP
    } state_e;

    state_e state;
    logic [7:0] data_reg;
    logic [3:0] bit_count;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            data_reg  <= 8'b0;
            bit_count <= 4'b0;
            out_byte  <= 8'b0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    if (!in) begin
                        state     <= DATA;
                        bit_count <= 4'b0;
                    end
                end

                DATA: begin
                    data_reg[bit_count] <= in;
                    if (bit_count == 4'd7) begin
                        state <= STOP;
                    end else begin
                        bit_count <= bit_count + 4'd1;
                    end
                end

                STOP: begin
                    if (in) begin
                        out_byte <= data_reg;
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
