module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    typedef enum logic [0:0] {
        STATE_A = 1'b0,
        STATE_B = 1'b1
    } state_t;

    state_t current_state, next_state;

    // State update logic with asynchronous reset
    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            current_state <= STATE_B; // Reset to state B
        end else begin
            current_state <= next_state;
        end
    end

    // Next state logic
    always_comb begin
        unique case (current_state)
            STATE_A: begin
                if (in) begin
                    next_state = STATE_A;
                end else begin
                    next_state = STATE_B;
                end
            end
            STATE_B: begin
                if (in) begin
                    next_state = STATE_B;
                end else begin
                    next_state = STATE_A;
                end
            end
        endcase
    end

    // Output logic
    always_comb begin
        case (current_state)
            STATE_A: out = 1'b0;
            STATE_B: out = 1'b1;
        endcase
    end

endmodule
