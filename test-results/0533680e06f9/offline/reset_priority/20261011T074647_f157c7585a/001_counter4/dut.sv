// OFFLINE TEST FIXTURE — not an LLM result.
module counter4(input wire clk,rst,en, output reg [3:0] q);
always @(posedge clk) begin
  if (en) q <= q + 1'b1;
  else if (rst) q <= 0;
end
endmodule
