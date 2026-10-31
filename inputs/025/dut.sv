module TopModule (
    input  logic clk,
    input  logic in,
    input  logic reset,
    output logic [7:0] out_byte,
    output logic done
);

    typedef enum logic [1:0] {
        IDLE  = 2'd0,
        DATA  = 2'd1,
        STOP  = 2'd2,
        WAIT  = 2'd3
    } state_t;

    state_t state, next_state;
    logic [7:0] shift_reg;
    logic [2:0] bit_cnt;
    logic [7:0] out_reg;

    // State register
    always_ff @(posedge clk) begin
        if (reset)
            state <= IDLE;
        else
            state <= next_state;
    end

    // Next-state logic
    always_comb begin
        next_state = state;
        case (state)
            IDLE: begin
                if (!in) next_state = DATA;
            end
            DATA: begin
                if (bit_cnt == 3'd7) next_state = STOP;
            end
            STOP: begin
                if (in) next_state = IDLE;
                else    next_state = WAIT;
            end
            WAIT: begin
                if (in) next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    // Data path: shift register and bit counter
    always_ff @(posedge clk) begin
        if (reset) begin
            shift_reg <= 8'd0;
            bit_cnt   <= 3'd0;
            out_reg   <= 8'd0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    bit_cnt <= 3'd0;
                    if (!in) begin
                        // start bit detected, initialize
                    end
                end
                DATA: begin
                    shift_reg <= {in, shift_reg[7:1]};
                    bit_cnt   <= bit_cnt + 3'd1;
                end
                STOP: begin
                    if (in) begin
                        out_reg <= {in, shift_reg[7:1]};
                        done    <= 1'b1;
                    end
                end
                WAIT: begin
                    // wait for stop bit (logic 1)
                end
                default: ;
            endcase
        end
    end

    assign out_byte = out_reg;

endmodule
