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

    logic [2:0] funded;
    logic [3:0] credit_plus_refund;

    always_comb begin
        credit_plus_refund = {1'b0, credit} + {2'b00, refund};
        funded = (credit_plus_refund > 4'd5)
               ? 3'd5
               : credit_plus_refund[2:0];

        can_pay = rst_n &&
                  (cost != 2'd0) &&
                  (funded >= {1'b0, cost});
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            credit   <= 3'd0;
            accepted <= 1'b0;
            rejected <= 1'b0;
        end else begin
            accepted <= 1'b0;
            rejected <= 1'b0;

            if (submit) begin
                if (cost == 2'd0) begin
                    credit   <= funded;
                    rejected <= 1'b1;
                end else if (funded >= {1'b0, cost}) begin
                    credit   <= funded - {1'b0, cost};
                    accepted <= 1'b1;
                end else begin
                    credit   <= funded;
                    rejected <= 1'b1;
                end
            end else begin
                credit <= funded;
            end
        end
    end

endmodule
