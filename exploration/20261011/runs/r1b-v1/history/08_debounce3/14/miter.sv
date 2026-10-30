module gold(input clk,input rst_n,input din,output q);
reg high;reg [1:0] streak; always @(posedge clk or negedge rst_n) if(!rst_n) begin high<=0;streak<=0;end else if(din==high) streak<=0;else if((!high && streak==2)||(high && streak==1)) begin high<=!high;streak<=0;end else streak<=streak+1; assign q=high;
endmodule
module gate(
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    localparam S0 = 3'd0;
    localparam S1 = 3'd1;
    localparam S2 = 3'd2;
    localparam S3 = 3'd3;
    localparam S4 = 3'd4;

    reg [2:0] state, next_state;

    always @(*) begin
        next_state = state;
        case (state)
            S0: begin
                if (din)
                    next_state = S1;
            end
            S1: begin
                if (din)
                    next_state = S2;
                else
                    next_state = S0;
            end
            S2: begin
                if (din)
                    next_state = S3;
                else
                    next_state = S0;
            end
            S3: begin
                if (!din)
                    next_state = S4;
            end
            S4: begin
                if (!din)
                    next_state = S0;
                else
                    next_state = S3;
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

    assign q = (state == S3) || (state == S4);

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
