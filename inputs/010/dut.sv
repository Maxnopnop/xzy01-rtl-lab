module TopModule (
    input  clk,
    input  areset,
    input  x,
    output reg z
);
    // State encoding
    typedef enum logic [1:0] {
        S0_IDLE      = 2'b00, // Waiting for first 1
        S1_COMPLEMENT= 2'b01  // Output complement
    } state_t;

    state_t state, next_state;

    // Sequential block for state and output
    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S0_IDLE;
            z     <= 1'b0;
        end else begin
            state <= next_state;
            // Moore output logic
            case (next_state)
                S0_IDLE:       z <= 1'b0;
                S1_COMPLEMENT: z <= ~x;
            endcase
        end
    end

    // Next state logic
    always_comb begin
        case (state)
            S0_IDLE: begin
                if (x == 1'b1)
                    next_state = S1_COMPLEMENT;
                else
                    next_state = S0_IDLE;
            end
            S1_COMPLEMENT: begin
                next_state = S1_COMPLEMENT;
            end
            default: next_state = S0_IDLE;
        endcase
    end
endmodule
