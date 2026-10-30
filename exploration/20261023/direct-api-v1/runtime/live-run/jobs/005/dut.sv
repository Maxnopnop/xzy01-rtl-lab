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
    logic [1:0] level_d;
    logic       dfr_q;
    logic       dfr_d;

    always_comb begin
        level_d = level_q;

        case (s)
            3'b000: level_d = 2'd0;
            3'b001: level_d = 2'd1;
            3'b011: level_d = 2'd2;
            3'b111: level_d = 2'd3;
            default: level_d = level_q;
        endcase

        dfr_d = dfr_q;

        if (level_d == 2'd0)
            dfr_d = 1'b1;
        else if (level_d == 2'd3)
            dfr_d = 1'b0;
        else if (level_d > level_q)
            dfr_d = 1'b1;
        else if (level_d < level_q)
            dfr_d = 1'b0;
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            level_q <= 2'd0;
            dfr_q   <= 1'b1;
        end else begin
            level_q <= level_d;
            dfr_q   <= dfr_d;
        end
    end

    always_comb begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;

        case (level_q)
            2'd0: begin
                fr2 = 1'b1;
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
            2'd1: begin
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
            2'd2: begin
                fr0 = 1'b1;
            end
            default: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
            end
        endcase

        dfr = dfr_q;
    end

endmodule
