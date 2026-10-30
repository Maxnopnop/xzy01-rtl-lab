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

    logic       a_valid, a_tag;
    logic [1:0] a_data;
    logic       b_valid, b_tag;
    logic [1:0] b_data;

    logic       updated_a_valid, updated_a_tag;
    logic [1:0] updated_a_data;
    logic       updated_b_valid, updated_b_tag;
    logic [1:0] updated_b_data;

    always_comb begin
        updated_a_valid = av | a_valid;
        updated_a_tag   = av ? atag  : a_tag;
        updated_a_data  = av ? adata : a_data;

        updated_b_valid = bv | b_valid;
        updated_b_tag   = bv ? btag  : b_tag;
        updated_b_data  = bv ? bdata : b_data;
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
            joined <= 1'b0;

            if (av) begin
                a_valid <= 1'b1;
                a_tag   <= atag;
                a_data  <= adata;
            end

            if (bv) begin
                b_valid <= 1'b1;
                b_tag   <= btag;
                b_data  <= bdata;
            end

            if (updated_a_valid && updated_b_valid &&
                (updated_a_tag == updated_b_tag)) begin
                a_valid <= 1'b0;
                b_valid <= 1'b0;
                joined  <= 1'b1;
                result  <= updated_a_data ^ updated_b_data;
            end
        end
    end

    assign pending_a = a_valid;
    assign pending_b = b_valid;

endmodule
