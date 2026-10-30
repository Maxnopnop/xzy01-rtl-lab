module gold(input clk,input rst_n,input din,output q);
reg [1:0] phase; always @(posedge clk or negedge rst_n) if(!rst_n) phase<=0; else if(phase==0) begin if(din) phase<=1;end else if(phase==1) phase<=2; else if(phase==2) phase<=3; else if(!din) phase<=0; assign q=phase==2;
endmodule
module gate(
    input clk,
    input rst_n,
    input din,
    output q
);

    localparam S_IDLE     = 2'b00;
    localparam S_DELAY    = 2'b01;
    localparam S_ASSERTED = 2'b10;
    localparam S_COOLDOWN = 2'b11;

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
        end else begin
            case (state)
                S_IDLE: begin
                    if (din)
                        state <= S_DELAY;
                    else
                        state <= S_IDLE;
                end
                S_DELAY: begin
                    state <= S_ASSERTED;
                end
                S_ASSERTED: begin
                    state <= S_COOLDOWN;
                end
                S_COOLDOWN: begin
                    if (din)
                        state <= S_COOLDOWN;
                    else
                        state <= S_IDLE;
                end
                default: begin
                    state <= S_IDLE;
                end
            endcase
        end
    end

    assign q = (state == S_ASSERTED);

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
