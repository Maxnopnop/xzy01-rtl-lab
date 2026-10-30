module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    typedef enum logic [1:0] {
        IDLE,
        DATA,
        STOP,
        WAIT_STOP
    } state_t;

    state_t state;
    logic [2:0] bit_count;

    assign done = (state == STOP) && in;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            bit_count <= 3'd0;
            out_byte  <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    if (!in) begin
                        state     <= DATA;
                        bit_count <= 3'd0;
                    end
                end

                DATA: begin
                    out_byte <= {in, out_byte[7:1]};
                    if (bit_count == 3'd7) begin
                        state <= STOP;
                    end else begin
                        bit_count <= bit_count + 3'd1;
                    end
                end

                STOP: begin
                    if (in)
                        state <= IDLE;
                    else
                        state <= WAIT_STOP;
                end

                WAIT_STOP: begin
                    if (in)
                        state <= IDLE;
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
