module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    logic state;
    logic next_state;

    always_comb begin
        case (state)
            1'b1: next_state = in ? 1'b1 : 1'b0;
            1'b0: next_state = in ? 1'b0 : 1'b1;
            default: next_state = 1'b1;
        endcase
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= 1'b1;
        else
            state <= next_state;
    end

    assign out = state;

endmodule
