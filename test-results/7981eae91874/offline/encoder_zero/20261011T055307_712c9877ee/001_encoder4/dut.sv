// OFFLINE TEST FIXTURE — not an LLM result.
module encoder4(input wire [3:0] req, output reg valid, output reg [1:0] index);
always @* begin
  valid = |req;
  if (req[3]) index = 3;
  else if (req[2]) index = 2;
  else if (req[1]) index = 1;
  else index = 1;
end
endmodule
