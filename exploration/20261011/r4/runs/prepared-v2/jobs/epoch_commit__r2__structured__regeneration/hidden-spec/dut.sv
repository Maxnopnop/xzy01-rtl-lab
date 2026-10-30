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
    logic       dirty0, dirty1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            live0     <= 2'b00;
            live1     <= 2'b00;
            staged0   <= 2'b00;
            staged1   <= 2'b00;
            dirty0    <= 1'b0;
            dirty1    <= 1'b0;
            committed <= 1'b0;
        end else begin
            committed <= 1'b0;

            if (abort_tx) begin
                staged0 <= live0;
                staged1 <= live1;
                dirty0  <= 1'b0;
                dirty1  <= 1'b0;
            end else if (commit) begin
                if (dirty0 || (write && !slot)) begin
                    live0 <= (write && !slot) ? data : staged0;
                end
                if (dirty1 || (write && slot)) begin
                    live1 <= (write && slot) ? data : staged1;
                end

                if (write && !slot) begin
                    staged0 <= data;
                end
                if (write && slot) begin
                    staged1 <= data;
                end

                dirty0    <= 1'b0;
                dirty1    <= 1'b0;
                committed <= 1'b1;
            end else if (write) begin
                if (slot) begin
                    staged1 <= data;
                    dirty1  <= 1'b1;
                end else begin
                    staged0 <= data;
                    dirty0  <= 1'b1;
                end
            end
        end
    end

    always_comb begin
        visible = rst_n ? (read_slot ? live1 : live0) : 2'b00;
        dirty   = {dirty1, dirty0};
    end

endmodule
