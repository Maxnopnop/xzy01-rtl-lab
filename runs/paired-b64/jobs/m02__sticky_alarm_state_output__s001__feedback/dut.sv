module sticky_alarm(
    input clk,
    input rst_n,
    input din,
    output q
);

    localparam S0 = 2'b00;
    localparam S1 = 2'b01;
    localparam S2 = 2'b10;

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S0;
        end else begin
            case (state)
                S0: begin
                    if (din)
                        state <= S1;
                    else
                        state <= S0;
                end
                S1: begin
                    if (din)
                        state <= S2;
                    else
                        state <= S0;
                end
                S2: begin
                    state <= S2;
                end
                default: begin
                    state <= S0;
                end
            endcase
        end
    end

    assign q = (state == S2);

endmodule
