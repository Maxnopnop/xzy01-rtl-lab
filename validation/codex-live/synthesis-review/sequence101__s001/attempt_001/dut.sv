module sequence101(
    input  wire clk,
    input  wire rst,
    input  wire din,
    output reg  match
);

    reg [1:0] history;
    reg [1:0] count;

    always @(posedge clk) begin
        if (rst) begin
            history <= 2'b00;
            count   <= 2'b00;
            match   <= 1'b0;
        end else begin
            match   <= (count == 2'b10) && (history == 2'b10) && din;
            history <= {history[0], din};
            if (count != 2'b10)
                count <= count + 1'b1;
        end
    end

endmodule
