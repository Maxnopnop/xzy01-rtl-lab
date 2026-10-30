module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] s,
    output logic       fr2,
    output logic       fr1,
    output logic       fr0,
    output logic       dfr
);

    logic [1:0] sensor_level;
    logic [1:0] current_level;

    always_comb begin
        case (s)
            3'b000: sensor_level = 2'd0;
            3'b001: sensor_level = 2'd1;
            3'b011: sensor_level = 2'd2;
            3'b111: sensor_level = 2'd3;
            default: sensor_level = 2'd0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            current_level <= 2'd0;
            dfr <= 1'b1;
        end else begin
            if (sensor_level != current_level)
                dfr <= (sensor_level > current_level);
            current_level <= sensor_level;
        end
    end

    always_comb begin
        fr2 = 1'b0;
        fr1 = 1'b0;
        fr0 = 1'b0;

        case (current_level)
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
            end
        endcase
    end

endmodule
