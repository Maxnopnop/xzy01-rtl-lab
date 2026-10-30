module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    typedef enum logic {A, B} state_t;
    state_t state, next_state;

    always_comb begin
        case (state)
            B:       next_state = in ? B : A;
            A:       next_state = in ? A : B;
            default: next_state = B;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= B;
        else
            state <= next_state;
    end

    always_comb begin
        case (state)
            B:       out = 1'b1;
            A:       out = 1'b0;
            default: out = 1'b1;
        endcase
    end

endmodule
