module gold(input clk,input rst_n,input din,output q);
reg high;reg [1:0] streak; always @(posedge clk or negedge rst_n) if(!rst_n) begin high<=0;streak<=0;end else if(din==high) streak<=0;else if((!high && streak==2)||(high && streak==1)) begin high<=!high;streak<=0;end else streak<=streak+1; assign q=high;
endmodule
module gate (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    reg [2:0] state;
    reg [2:0] next_state;

    localparam S_LOW   = 3'd0;
    localparam S_ONE   = 3'd1;
    localparam S_TWO   = 3'd2;
    localparam S_HIGH  = 3'd3;
    localparam S_ZERO  = 3'd4;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S_LOW;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            S_LOW: begin
                if (din)
                    next_state = S_ONE;
                else
                    next_state = S_LOW;
            end
            S_ONE: begin
                if (din)
                    next_state = S_TWO;
                else
                    next_state = S_LOW;
            end
            S_TWO: begin
                if (din)
                    next_state = S_HIGH;
                else
                    next_state = S_LOW;
            end
            S_HIGH: begin
                if (din)
                    next_state = S_HIGH;
                else
                    next_state = S_ZERO;
            end
            S_ZERO: begin
                if (din)
                    next_state = S_HIGH;
                else
                    next_state = S_LOW;
            end
            default: next_state = S_LOW;
        endcase
    end

    assign q = (state == S_HIGH) || (state == S_ZERO);

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
