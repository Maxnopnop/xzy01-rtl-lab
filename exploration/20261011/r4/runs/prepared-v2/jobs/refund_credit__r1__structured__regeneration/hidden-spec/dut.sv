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

    logic [3:0] sum;
    logic [3:0] funded;

    always_comb begin
        sum = {1'b0, credit} + {2'b00, refund};

        if (sum > 4'd5)
            funded = 4'd5;
        else
            funded = sum;

        can_pay = rst_n &&
                  (cost != 2'd0) &&
                  (funded >= {2'b00, cost});
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            credit   <= 3'd0;
            accepted <= 1'b0;
            rejected <= 1'b0;
        end else begin
            credit   <= funded[2:0];
            accepted <= 1'b0;
            rejected <= 1'b0;

            if (submit) begin
                if (cost == 2'd0) begin
                    rejected <= 1'b1;
                end else if (funded >= {2'b00, cost}) begin
                    credit   <= funded[2:0] - {1'b0, cost};
                    accepted <= 1'b1;
                end else begin
                    rejected <= 1'b1;
                end
            end
        end
    end

endmodule
