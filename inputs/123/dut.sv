module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    logic [2:0] s_prev;

    always_ff @(posedge clk) begin
        if (reset) begin
            s_prev <= 3'b000;
        end else begin
            s_prev <= s;
        end
    end

    always_comb begin
        fr2 = ~(s[2] | s[1] | s[0]);
        fr1 = ~(s[2] | s[1]);
        fr0 = ~s[2];

        dfr = 1'b0;
        if (s != s_prev) begin
            if ((s[2] & ~s[1] & ~s[0]) ||
                (s[2] & s[1] & ~s[0]) ||
                (~s[2] & s[1] & ~s[0])) begin
                dfr = 1'b1;
            end
        end

        if (reset) begin
            fr2 = 1'b1;
            fr1 = 1'b1;
            fr0 = 1'b1;
            dfr = 1'b1;
        end
    end

endmodule
