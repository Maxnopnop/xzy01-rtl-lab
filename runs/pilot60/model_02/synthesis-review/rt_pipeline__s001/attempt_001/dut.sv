module multi_pipe_4bit #(
    parameter size = 4
) (
    input  logic                  clk,
    input  logic                  rst_n,
    input  logic [size-1:0]       mul_a,
    input  logic [size-1:0]       mul_b,
    output logic [(2*size)-1:0]   mul_out
);

    logic [(2*size)-1:0] partial_products [0:size-1];
    logic [(2*size)-1:0] sum_reg [0:size-1];

    genvar i;
    generate
        for (i = 0; i < size; i = i + 1) begin : gen_partial_products
            always_comb begin
                if (mul_b[i])
                    partial_products[i] = {{size{1'b0}}, mul_a} << i;
                else
                    partial_products[i] = '0;
            end
        end
    endgenerate

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_reg[0] <= '0;
            sum_reg[1] <= '0;
            sum_reg[2] <= '0;
            sum_reg[3] <= '0;
        end else begin
            sum_reg[0] <= partial_products[0];
            sum_reg[1] <= partial_products[1];
            sum_reg[2] <= partial_products[2];
            sum_reg[3] <= partial_products[3];
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mul_out <= '0;
        else
            mul_out <= sum_reg[0] + sum_reg[1] + sum_reg[2] + sum_reg[3];
    end

endmodule
