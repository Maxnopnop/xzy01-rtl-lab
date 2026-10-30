module escape_frame (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       feed,
    input  wire [1:0] symbol,
    input  wire       flush,
    output reg        active,
    output reg        escaped,
    output reg  [1:0] work_sum,
    output reg  [1:0] work_count,
    output reg  [1:0] last_sum,
    output reg  [1:0] last_count,
    output reg        completed
);

    localparam [1:0] START = 2'd0;
    localparam [1:0] END   = 2'd1;
    localparam [1:0] ESC   = 2'd2;
    localparam [1:0] DATA  = 2'd3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active     <= 1'b0;
            escaped    <= 1'b0;
            work_sum   <= 2'd0;
            work_count <= 2'd0;
            last_sum   <= 2'd0;
            last_count <= 2'd0;
            completed  <= 1'b0;
        end else begin
            completed <= 1'b0;

            if (flush) begin
                active     <= 1'b0;
                escaped    <= 1'b0;
                work_sum   <= 2'd0;
                work_count <= 2'd0;
            end else if (feed) begin
                if (!active) begin
                    if (symbol == START) begin
                        active     <= 1'b1;
                        escaped    <= 1'b0;
                        work_sum   <= 2'd0;
                        work_count <= 2'd0;
                    end
                end else if (escaped) begin
                    work_sum   <= work_sum ^ symbol;
                    work_count <= work_count + 2'd1;
                    escaped    <= 1'b0;
                end else begin
                    case (symbol)
                        START: begin
                            work_sum   <= 2'd0;
                            work_count <= 2'd0;
                            escaped    <= 1'b0;
                        end

                        END: begin
                            active     <= 1'b0;
                            escaped    <= 1'b0;
                            work_sum   <= 2'd0;
                            work_count <= 2'd0;
                            last_sum   <= work_sum;
                            last_count <= work_count;
                            completed  <= 1'b1;
                        end

                        ESC: begin
                            escaped <= 1'b1;
                        end

                        DATA: begin
                            work_sum   <= work_sum ^ DATA;
                            work_count <= work_count + 2'd1;
                        end
                    endcase
                end
            end
        end
    end

endmodule
