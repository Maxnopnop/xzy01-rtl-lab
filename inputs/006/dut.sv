module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [2:0]  s,
    output logic        fr2,
    output logic        fr1,
    output logic        fr0,
    output logic        dfr
);

    typedef enum logic [1:0] {
        LEVEL_BELOW_S0,
        LEVEL_BETWEEN_S1_S0,
        LEVEL_BETWEEN_S2_S1,
        LEVEL_ABOVE_S2
    } state_e;

    state_e state_q, state_d;

    always_comb begin
        unique case (s)
            3'b000:   state_d = LEVEL_BELOW_S0;
            3'b001:   state_d = LEVEL_BETWEEN_S1_S0;
            3'b011:   state_d = LEVEL_BETWEEN_S2_S1;
            3'b111:   state_d = LEVEL_ABOVE_S2;
            default:  state_d = LEVEL_BELOW_S0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state_q <= LEVEL_BELOW_S0;
        end else begin
            state_q <= state_d;
        end
    end

    always_comb begin
        unique case (state_q)
            LEVEL_BELOW_S0: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b1;
                dfr = 1'b1;
            end
            LEVEL_BETWEEN_S1_S0: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b0;
                dfr = 1'b0;
            end
            LEVEL_BETWEEN_S2_S1: begin
                fr0 = 1'b1;
                fr1 = 1'b0;
                fr2 = 1'b0;
                dfr = 1'b0;
            end
            LEVEL_ABOVE_S2: begin
                fr0 = 1'b0;
                fr1 = 1'b0;
                fr2 = 1'b0;
                dfr = 1'b0;
            end
            default: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b1;
                dfr = 1'b1;
            end
        endcase
    end

endmodule
