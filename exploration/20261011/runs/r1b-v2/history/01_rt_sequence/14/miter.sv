module gold(input clk,input rst_n,input din,output q);
reg [3:0] history; always @(posedge clk or negedge rst_n) if(!rst_n) history<=0; else history<={history[2:0],din}; assign q=history==4'b1001;
endmodule
module gate (
    input  wire clk,
    input  wire rst_n,
    input  wire data_in,
    output reg  sequence_detected
);

    localparam [2:0] IDLE = 3'd0,
                     S1   = 3'd1,
                     S2   = 3'd2,
                     S3   = 3'd3,
                     S4   = 3'd4;

    reg [2:0] state, next_state;

    always @(*) begin
        case (state)
            IDLE: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = IDLE;
            end
            S1: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = S2;
            end
            S2: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = S3;
            end
            S3: begin
                if (data_in)
                    next_state = S4;
                else
                    next_state = IDLE;
            end
            S4: begin
                if (data_in)
                    next_state = S1;
                else
                    next_state = S3;
            end
            default: next_state = IDLE;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            sequence_detected <= 1'b0;
        end else begin
            state <= next_state;
            if (next_state == S4)
                sequence_detected <= 1'b1;
            else
                sequence_detected <= 1'b0;
        end
    end

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.data_in(din),.sequence_detected(a));assign mismatch=g^a;endmodule
