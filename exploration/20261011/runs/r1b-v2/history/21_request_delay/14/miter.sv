module gold(input clk,input rst_n,input din,output q);
reg [1:0] phase; always @(posedge clk or negedge rst_n) if(!rst_n) phase<=0; else if(phase==0) begin if(din) phase<=1;end else if(phase==1) phase<=2; else if(phase==2) phase<=3; else if(!din) phase<=0; assign q=phase==2;
endmodule
module gate (
    input  clk,
    input  rst_n,
    input  din,
    output reg q
);

    reg [1:0] state;
    reg [1:0] next_state;

    localparam IDLE     = 2'b00;
    localparam WAIT_ONE = 2'b01;
    localparam PULSE    = 2'b10;
    localparam COOLDOWN = 2'b11;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = IDLE;
        case (state)
            IDLE: begin
                if (din)
                    next_state = WAIT_ONE;
                else
                    next_state = IDLE;
            end
            WAIT_ONE: begin
                next_state = PULSE;
            end
            PULSE: begin
                next_state = COOLDOWN;
            end
            COOLDOWN: begin
                if (din)
                    next_state = COOLDOWN;
                else
                    next_state = IDLE;
            end
            default: begin
                next_state = IDLE;
            end
        endcase
    end

    always @(*) begin
        q = 1'b0;
        case (state)
            PULSE: q = 1'b1;
            default: q = 1'b0;
        endcase
    end

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.din(din),.q(a));assign mismatch=g^a;endmodule
