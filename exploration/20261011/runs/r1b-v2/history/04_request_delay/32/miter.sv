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
    localparam IDLE     = 2'b00;
    localparam RESPONSE = 2'b01;
    localparam COOLDOWN = 2'b10;

    assign q = (state == RESPONSE);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            case (state)
                IDLE: begin
                    if (din)
                        state <= RESPONSE;
                    else
                        state <= IDLE;
                end
                RESPONSE: begin
                    state <= COOLDOWN;
                end
                COOLDOWN: begin
                    if (din)
                        state <= COOLDOWN;
                    else
                        state <= IDLE;
                end
                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
