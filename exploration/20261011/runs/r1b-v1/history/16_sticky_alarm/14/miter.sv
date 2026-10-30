module gold(input clk,input rst_n,input din,output q);
reg previous,alarm; always @(posedge clk or negedge rst_n) if(!rst_n) begin previous<=0;alarm<=0;end else begin previous<=din;alarm<=alarm|(previous&din);end assign q=alarm;
endmodule
module gate(
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    localparam [1:0] S0 = 2'b00;
    localparam [1:0] S1 = 2'b01;
    localparam [1:0] S2 = 2'b10;

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
                S2: state <= S2;
                default: state <= S0;
            endcase
        end
    end

    assign q = (state == S2);

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
