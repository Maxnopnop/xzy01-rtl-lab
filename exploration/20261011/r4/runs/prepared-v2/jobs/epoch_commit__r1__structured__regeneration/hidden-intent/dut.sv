module epoch_commit (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       write,
    input  logic       slot,
    input  logic [1:0] data,
    input  logic       commit,
    input  logic       abort_tx,
    input  logic       read_slot,
    output logic [1:0] visible,
    output logic [1:0] dirty,
    output logic       committed
);

    logic [1:0] live0, live1;
    logic [1:0] staged0, staged1;
    logic [1:0] dirty_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            live0      <= 2'b00;
            live1      <= 2'b00;
            staged0    <= 2'b00;
            staged1    <= 2'b00;
            dirty_reg  <= 2'b00;
            committed  <= 1'b0;
        end else begin
            committed <= 1'b0;

            if (abort_tx) begin
                staged0   <= live0;
                staged1   <= live1;
                dirty_reg <= 2'b00;
            end else begin
                if (write) begin
                    if (slot == 1'b0) begin
                        staged0     <= data;
                        dirty_reg[0] <= 1'b1;
                    end else begin
                        staged1     <= data;
                        dirty_reg[1] <= 1'b1;
                    end
                end

                if (commit) begin
                    if (dirty_reg[0] || (write && (slot == 1'b0)))
                        live0 <= (write && (slot == 1'b0)) ? data : staged0;

                    if (dirty_reg[1] || (write && (slot == 1'b1)))
                        live1 <= (write && (slot == 1'b1)) ? data : staged1;

                    dirty_reg <= 2'b00;
                    committed <= 1'b1;
                end
            end
        end
    end

    always_comb begin
        if (!rst_n)
            visible = 2'b00;
        else if (read_slot == 1'b0)
            visible = live0;
        else
            visible = live1;
    end

    assign dirty = dirty_reg;

endmodule
