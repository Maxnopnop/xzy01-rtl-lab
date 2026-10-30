module tagged_join (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       clear,
    input  wire       a_valid,
    input  wire [1:0] a_tag,
    input  wire [1:0] a_data,
    input  wire       b_valid,
    input  wire [1:0] b_tag,
    input  wire [1:0] b_data,
    input  wire       take,
    output reg        a_full,
    output reg        b_full,
    output reg        out_valid,
    output reg  [1:0] out_tag,
    output reg  [3:0] out_data
);

    reg [1:0] a_tag_r;
    reg [1:0] a_data_r;
    reg [1:0] b_tag_r;
    reg [1:0] b_data_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_full    <= 1'b0;
            a_tag_r   <= 2'b00;
            a_data_r  <= 2'b00;
            b_full    <= 1'b0;
            b_tag_r   <= 2'b00;
            b_data_r  <= 2'b00;
            out_valid <= 1'b0;
            out_tag   <= 2'b00;
            out_data  <= 4'b0000;
        end else if (clear) begin
            a_full    <= 1'b0;
            a_tag_r   <= 2'b00;
            a_data_r  <= 2'b00;
            b_full    <= 1'b0;
            b_tag_r   <= 2'b00;
            b_data_r  <= 2'b00;
            out_valid <= 1'b0;
            out_tag   <= 2'b00;
            out_data  <= 4'b0000;
        end else begin
            if (!a_full && a_valid) begin
                a_full   <= 1'b1;
                a_tag_r  <= a_tag;
                a_data_r <= a_data;
            end

            if (!b_full && b_valid) begin
                b_full   <= 1'b1;
                b_tag_r  <= b_tag;
                b_data_r <= b_data;
            end

            if (take)
                out_valid <= 1'b0;

            if (a_full && b_full) begin
                if (a_tag_r < b_tag_r) begin
                    a_full <= 1'b0;
                end else if (a_tag_r > b_tag_r) begin
                    b_full <= 1'b0;
                end else if (!out_valid || take) begin
                    a_full    <= 1'b0;
                    b_full    <= 1'b0;
                    out_valid <= 1'b1;
                    out_tag   <= a_tag_r;
                    out_data  <= {a_data_r, b_data_r};
                end
            end
        end
    end

endmodule
