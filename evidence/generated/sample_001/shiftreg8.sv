module shiftreg8 (
    input  wire       clk,
    input  wire       rst,
    input  wire       en,
    input  wire       serial_in,
    output reg  [7:0] q
);

    always @(posedge clk) begin
        if (rst)
            q <= 8'b0;
        else if (en)
            q <= {q[6:0], serial_in};
    end

endmodule
