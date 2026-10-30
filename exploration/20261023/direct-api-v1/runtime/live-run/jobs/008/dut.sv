module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    logic [1:0] level_q, level_d;
    logic       dfr_q, dfr_d;
    logic [1:0] sensed_level;

    always_comb begin
        sensed_level = level_q;

        case (s)
            3'b000: sensed_level = 2'd0;
            3'b001: sensed_level = 2'd1;
            3'b011: sensed_level = 2'd2;
            3'b111: sensed_level = 2'd3;
            default: sensed_level = level_q;
        endcase

        level_d = level_q;
        dfr_d   = dfr_q;

        if (sensed_level != level_q) begin
            level_d = sensed_level;
            dfr_d   = (sensed_level > level_q);
        end
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
        dfr = dfr_q;

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
            2'd3: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
            end
            default: begin
                fr2 = 1'b1;
                fr1 = 1'b1;
                fr0 = 1'b1;
                dfr = 1'b1;
            end
        endcase
    end

endmodule
