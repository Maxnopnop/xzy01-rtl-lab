module multi_pipe_4bit #(
    parameter integer size = 4
) (
    input  logic                  clk,
    input  logic                  rst_n,
    input  logic [size-1:0]       mul_a,
    input  logic [size-1:0]       mul_b,
    output logic [(2*size)-1:0]   mul_out
);

    logic [(2*size)-1:0] mul_a_ext;
    logic [(2*size)-1:0] partial_product [0:size-1];
    logic [(2*size)-1:0] sum_reg_0;
    logic [(2*size)-1:0] sum_reg_1;

    assign mul_a_ext = {{size{1'b0}}, mul_a};

    genvar i;
    generate
        for (i = 0; i < size; i = i + 1) begin : gen_partial_products
            assign partial_product[i] =
                mul_b[i] ? (mul_a_ext << i) : {(2*size){1'b0}};
        end
    endgenerate

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_reg_0 <= {(2*size){1'b0}};
            sum_reg_1 <= {(2*size){1'b0}};
        end else begin
            sum_reg_0 <= partial_product[0] + partial_product[1];
            sum_reg_1 <= partial_product[2] + partial_product[3];
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mul_out <= {(2*size){1'b0}};
        else
            mul_out <= sum_reg_0 + sum_reg_1;
    end

endmodule
