module gold(input clk,input rst_n,input din,output q);
reg parity; always @(posedge clk or negedge rst_n) if(!rst_n) parity<=0; else parity<=parity^din; assign q=parity;
endmodule
module gate (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    localparam S0 = 1'b0;
    localparam S1 = 1'b1;

    reg state;
    reg next_state;

    always @(*) begin
        case (state)
            S0: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S0;
            end
            S1: begin
                if (din)
                    next_state = S0;
                else
                    next_state = S1;
            end
            default: next_state = S0;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    assign q = (state == S1);

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
