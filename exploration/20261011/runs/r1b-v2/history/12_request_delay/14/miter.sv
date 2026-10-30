module gold(input clk,input rst_n,input din,output q);
reg [1:0] phase; always @(posedge clk or negedge rst_n) if(!rst_n) phase<=0; else if(phase==0) begin if(din) phase<=1;end else if(phase==1) phase<=2; else if(phase==2) phase<=3; else if(!din) phase<=0; assign q=phase==2;
endmodule
module gate (
    input  clk,
    input  rst_n,
    input  din,
    output q
);

    reg [1:0] state;
    localparam S_IDLE = 2'd0;
    localparam S_WAIT = 2'd1;
    localparam S_HIGH = 2'd2;
    localparam S_COOL = 2'd3;

    assign q = (state == S_HIGH);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
        end else begin
            case (state)
                S_IDLE: begin
                    if (din)
                        state <= S_WAIT;
                    else
                        state <= S_IDLE;
                end
                S_WAIT: begin
                    state <= S_HIGH;
                end
                S_HIGH: begin
                    state <= S_COOL;
                end
                S_COOL: begin
                    if (din)
                        state <= S_COOL;
                    else
                        state <= S_IDLE;
                end
                default: begin
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
