module TopModule (
    input  logic       clk,
    input  logic       in,
    input  logic       reset,
    output logic [7:0] out_byte,
    output logic       done
);

    localparam logic [1:0] IDLE  = 2'b00;
    localparam logic [1:0] DATA  = 2'b01;
    localparam logic [1:0] STOP  = 2'b10;
    localparam logic [1:0] ERROR = 2'b11;

    logic [1:0] state;
    logic [2:0] bit_count;
    logic [7:0] data_shift;

    always_ff @(posedge clk) begin
        if (reset) begin
            state      <= IDLE;
            bit_count  <= 3'd0;
            data_shift <= 8'd0;
            out_byte   <= 8'd0;
            done       <= 1'b0;
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
                    data_shift[bit_count] <= in;
                    if (bit_count == 3'd7) begin
                        state <= STOP;
                    end else begin
                        bit_count <= bit_count + 3'd1;
                    end
                end

                STOP: begin
                    if (in) begin
                        out_byte <= data_shift;
                        done     <= 1'b1;
                        state    <= IDLE;
                    end else begin
                        state <= ERROR;
                    end
                end

                ERROR: begin
                    if (in) begin
                        state <= IDLE;
                    end
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
