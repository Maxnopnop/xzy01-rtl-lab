module tagged_join (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       av,
    input  logic       atag,
    input  logic [1:0] adata,
    input  logic       bv,
    input  logic       btag,
    input  logic [1:0] bdata,
    input  logic       flush,
    output logic       pending_a,
    output logic       pending_b,
    output logic       joined,
    output logic [1:0] result
);

    logic       a_valid;
    logic       a_tag;
    logic [1:0] a_data;
    logic       b_valid;
    logic       b_tag;
    logic [1:0] b_data;

    logic       next_a_valid;
    logic       next_a_tag;
    logic [1:0] next_a_data;
    logic       next_b_valid;
    logic       next_b_tag;
    logic [1:0] next_b_data;

    always_comb begin
        next_a_valid = av ? 1'b1 : a_valid;
        next_a_tag   = av ? atag : a_tag;
        next_a_data  = av ? adata : a_data;

        next_b_valid = bv ? 1'b1 : b_valid;
        next_b_tag   = bv ? btag : b_tag;
        next_b_data  = bv ? bdata : b_data;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_valid <= 1'b0;
            a_tag   <= 1'b0;
            a_data  <= 2'b00;
            b_valid <= 1'b0;
            b_tag   <= 1'b0;
            b_data  <= 2'b00;
            joined  <= 1'b0;
            result  <= 2'b00;
        end else if (flush) begin
            a_valid <= 1'b0;
            a_tag   <= 1'b0;
            a_data  <= 2'b00;
            b_valid <= 1'b0;
            b_tag   <= 1'b0;
            b_data  <= 2'b00;
            joined  <= 1'b0;
            result  <= 2'b00;
        end else begin
            a_tag   <= next_a_tag;
            a_data  <= next_a_data;
            b_tag   <= next_b_tag;
            b_data  <= next_b_data;
            joined  <= 1'b0;

            if (next_a_valid && next_b_valid &&
                (next_a_tag == next_b_tag)) begin
                a_valid <= 1'b0;
                b_valid <= 1'b0;
                joined  <= 1'b1;
                result  <= next_a_data ^ next_b_data;
            end else begin
                a_valid <= next_a_valid;
                b_valid <= next_b_valid;
            end
        end
    end

    assign pending_a = a_valid;
    assign pending_b = b_valid;

endmodule
