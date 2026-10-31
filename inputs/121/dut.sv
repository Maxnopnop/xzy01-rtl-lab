module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    logic [2:0] s_prev;

    always_ff @(posedge clk) begin
        if (reset) begin
            s_prev <= 3'b000;
        end else begin
            s_prev <= s;
        end
    end

    always_comb begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;
        dfr = 1'b0;

        case (s)
            3'b111: begin
                fr2 = 1'b0;
                fr1 = 1'b0;
                fr0 = 1'b0;
            end

            3'b011: begin
                fr0 = 1'b1;
            end

            3'b001: begin
                fr1 = 1'b1;
                fr0 = 1'b1;
            end

            default: begin
                fr2 = 1'b1;
                fr1 = 1'b1;
                fr0 = 1'b1;
            end
        endcase

        if (s < s_prev)
            dfr = 1'b1;
    end

endmodule
