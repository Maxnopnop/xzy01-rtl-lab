module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    logic state_q, state_d;

    always_comb begin
        if (state_q) begin
            state_d = in ? 1'b1 : 1'b0;
        end else begin
            state_d = in ? 1'b0 : 1'b1;
        end
    end

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state_q <= 1'b1;
        else
            state_q <= state_d;
    end

    assign out = state_q;

endmodule
