module gold(input clk,input rst_n,input din,output q);
reg [3:0] history; always @(posedge clk or negedge rst_n) if(!rst_n) history<=0; else history<={history[2:0],din}; assign q=history==4'b1001;
endmodule
module gate (
    input  wire clk,
    input  wire rst_n,
    input  wire data_in,
    output reg  sequence_detected
);

    localparam [2:0] IDLE = 3'd0;
    localparam [2:0] S1   = 3'd1;
    localparam [2:0] S2   = 3'd2;
    localparam [2:0] S3   = 3'd3;
    localparam [2:0] S4   = 3'd4;

    reg [2:0] state;
    reg [2:0] next_state;

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: if (data_in) next_state = S1;
            S1:   if (data_in) next_state = S1;
                  else         next_state = S2;
            S2:   if (data_in) next_state = S1;
                  else         next_state = S3;
            S3:   if (data_in) next_state = S4;
                  else         next_state = IDLE;
            S4:   if (data_in) next_state = S1;
                  else         next_state = S2;
            default:           next_state = IDLE;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    always @(*) begin
        sequence_detected = (state == S4);
    end

endmodule

module miter(input clk,input rst_n,input din,output mismatch);wire g,a;gold G(.clk(clk),.rst_n(rst_n),.din(din),.q(g));gate A(.clk(clk),.rst_n(rst_n),.data_in(din),.sequence_detected(a));assign mismatch=g^a;endmodule
