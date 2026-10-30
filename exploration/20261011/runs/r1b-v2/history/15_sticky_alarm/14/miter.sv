module gold(input clk,input rst_n,input din,output q);
reg previous,alarm; always @(posedge clk or negedge rst_n) if(!rst_n) begin previous<=0;alarm<=0;end else begin previous<=din;alarm<=alarm|(previous&din);end assign q=alarm;
endmodule
module gate (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    localparam S0 = 2'b00;
    localparam S1 = 2'b01;
    localparam S2 = 2'b10;

    reg [1:0] state;
    reg [1:0] next_state;
    reg q;

    always @(*) begin
        next_state = state;
        case (state)
            S0: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S0;
            end
            S1: begin
                if (din)
                    next_state = S2;
                else
                    next_state = S0;
            end
            S2: begin
                next_state = S2;
            end
            default: begin
                next_state = S0;
            end
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            S2:      q = 1'b1;
            default: q = 1'b0;
        endcase
    end

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
