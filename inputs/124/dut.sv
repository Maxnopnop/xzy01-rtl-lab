module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic x,
    output logic z
);

    typedef enum logic [1:0] {
        ST_IDLE  = 2'b00,
        ST_INVERT = 2'b01,
        ST_PASS = 2'b10
    } state_t;
    
    state_t current_state, next_state;
    logic complement_bit;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            current_state <= ST_IDLE;
        end else begin
            current_state <= next_state;
        end
    end

    always_comb begin
        // Default assignments
        next_state = current_state;
        complement_bit = x;

        case (current_state)
            ST_IDLE: begin
                // Wait for reset to be released
                if (~areset) begin
                    if (x == 1'b1) begin
                        next_state = ST_INVERT;
                        complement_bit = 1'b0;
                    end else begin
                        next_state = ST_PASS;
                        complement_bit = 1'b1;
                    end
                end
            end
            ST_INVERT: begin
                complement_bit = ~x;
                // Remain in this state
            end
            ST_PASS: begin
                complement_bit = x;
                // Remain in this state
            end
            default: begin
                next_state = ST_IDLE;
            end
        endcase 
    end

    assign z = complement_bit;

endmodule
