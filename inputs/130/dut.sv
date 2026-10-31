module TopModule (
    input  clk,
    input areset,
    input x,
    output z
);

    typedef enum logic [1:0] {
        S_COPY = 2'b00,
        S_INVERT = 2'b01
    } state_t;

    state_t state, next_state;

    always_comb begin
        case (state)
            S_COPY: begin
                if (x) begin
                    next_state = S_INVERT;
                end else begin
                    next_state = S_COPY;
                end
            end
            default: begin
                next_state = S_INVERT;
            end
        endcase
    end

    always_comb begin
        case (state)
            S_COPY:   z = x;
            S_INVERT: z = ~x;
            default:  z = 1'b0;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S_COPY;
        end else begin
            state <= next_state;
        end
    end

endmodule
