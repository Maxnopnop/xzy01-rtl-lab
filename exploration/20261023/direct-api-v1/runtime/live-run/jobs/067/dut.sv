module TopModule (
    input        clk,
    input        in,
    input        reset,
    output logic [7:0] out_byte,
    output logic  done
);

    typedef enum logic [1:0] {
        IDLE,
        DATA,
        STOP
    } state_t;

    state_t state;
    logic [2:0] bit_count;
    logic [7:0] data_byte;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            bit_count <= 3'd0;
            data_byte <= 8'd0;
            out_byte  <= 8'd0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    if (!in) begin
                        state     <= DATA;
                        bit_count <= 3'd0;
                    end
                end

                DATA: begin
                    data_byte[bit_count] <= in;
                    if (bit_count == 3'd7) begin
                        state <= STOP;
                    end else begin
                        bit_count <= bit_count + 3'd1;
                    end
                end

                STOP: begin
                    if (in) begin
                        out_byte <= data_byte;
                        done     <= 1'b1;
                        state    <= IDLE;
                    end
                end

                default: begin
                    state     <= IDLE;
                    bit_count <= 3'd0;
                end
            endcase
        end
    end

endmodule
