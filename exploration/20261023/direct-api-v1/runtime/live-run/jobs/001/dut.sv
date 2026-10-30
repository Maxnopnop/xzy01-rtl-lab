module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    logic [1:0] level_q;
    logic [1:0] sensed_level;

    always_comb begin
        case (s)
            3'b000: sensed_level = 2'd0;
            3'b001: sensed_level = 2'd1;
            3'b011: sensed_level = 2'd2;
            3'b111: sensed_level = 2'd3;
            default: sensed_level = 2'd0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            level_q <= 2'd0;
            dfr     <= 1'b1;
        end else begin
            level_q <= sensed_level;
            if (sensed_level > level_q)
                dfr <= 1'b1;
            else if (sensed_level < level_q)
                dfr <= 1'b0;
        end
    end

    always_comb begin
        case (level_q)
            2'd0: begin
                fr2 = 1'b1;
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
            2'd1: begin
                fr2 = 1'b0;
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
            2'd2: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b1;
            end
            default: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
            end
        endcase
    end

endmodule
