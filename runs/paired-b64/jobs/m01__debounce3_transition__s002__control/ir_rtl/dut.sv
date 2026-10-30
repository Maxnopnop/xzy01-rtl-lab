module debounce3 (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    reg [2:0] state;

    localparam S0 = 3'd0,
               S1 = 3'd1,
               S2 = 3'd2,
               S3 = 3'd3,
               S4 = 3'd4;

    assign q = (state == S3) || (state == S4);

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
                    if (din)
                        state <= S3;
                    else
                        state <= S0;
                end
                S3: begin
                    if (din)
                        state <= S3;
                    else
                        state <= S4;
                end
                S4: begin
                    if (din)
                        state <= S3;
                    else
                        state <= S0;
                end
                default: state <= S0;
            endcase
        end
    end

endmodule
