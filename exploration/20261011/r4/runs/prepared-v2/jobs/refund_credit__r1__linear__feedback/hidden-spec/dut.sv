module refund_credit (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       submit,
    input  logic [1:0] refund,
    input  logic [1:0] cost,
    output logic [2:0] credit,
    output logic       accepted,
    output logic       rejected,
    output logic       can_pay
);

    logic [2:0] credit_reg;
    logic       accepted_reg;
    logic       rejected_reg;
    logic [3:0] credit_sum;
    logic [3:0] funded;

    always_comb begin
        credit_sum = {1'b0, credit_reg} + {2'b00, refund};
        funded = (credit_sum > 4'd5) ? 4'd5 : credit_sum;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            credit_reg   <= 3'd0;
            accepted_reg <= 1'b0;
            rejected_reg <= 1'b0;
        end else begin
            credit_reg   <= funded[2:0];
            accepted_reg <= 1'b0;
            rejected_reg <= 1'b0;

            if (submit) begin
                if (cost == 2'd0) begin
                    rejected_reg <= 1'b1;
                end else if (funded >= {2'b00, cost}) begin
                    credit_reg   <= funded[2:0] - {1'b0, cost};
                    accepted_reg <= 1'b1;
                end else begin
                    rejected_reg <= 1'b1;
                end
            end
        end
    end

    always_comb begin
        credit   = credit_reg;
        accepted = accepted_reg;
        rejected = rejected_reg;
        can_pay  = rst_n &&
                   (cost != 2'd0) &&
                   (funded >= {2'b00, cost});
    end

endmodule
