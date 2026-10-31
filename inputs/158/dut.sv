module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    typedef enum logic [3:0] {
        Idle,
        Data0,
        Data1,
        Data2,
        Data3,
        Data4,
        Data5,
        Data6,
        Data7,
        Stop
    } state_t;

    state_t state;
    logic [7:0] data_reg;

    always_ff @(posedge clk) begin
        if (reset) begin
            state     <= Idle;
            data_reg  <= 8'b0;
            out_byte  <= 8'b0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;

            case (state)
                Idle: begin
                    if (!in)
                        state <= Data0;
                end

                Data0: begin
                    data_reg[0] <= in;
                    state <= Data1;
                end

                Data1: begin
                    data_reg[1] <= in;
                    state <= Data2;
                end

                Data2: begin
                    data_reg[2] <= in;
                    state <= Data3;
                end

                Data3: begin
                    data_reg[3] <= in;
                    state <= Data4;
                end

                Data4: begin
                    data_reg[4] <= in;
                    state <= Data5;
                end

                Data5: begin
                    data_reg[5] <= in;
                    state <= Data6;
                end

                Data6: begin
                    data_reg[6] <= in;
                    state <= Data7;
                end

                Data7: begin
                    data_reg[7] <= in;
                    state <= Stop;
                end

                Stop: begin
                    if (in) begin
                        out_byte <= data_reg;
                        done <= 1'b1;
                        state <= Idle;
                    end
                end

                default: begin
                    state <= Idle;
                end
            endcase
        end
    end

endmodule
