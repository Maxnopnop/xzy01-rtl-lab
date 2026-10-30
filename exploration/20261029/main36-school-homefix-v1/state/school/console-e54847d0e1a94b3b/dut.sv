module TopModule (
  input  logic         clk,
  input  logic         load,
  input  logic [511:0] data,
  output logic [511:0] q
);

  logic [511:0] next_q;

  always_comb begin
    next_q = (q & ~(q >> 1 & q << 1)) | (~q & (q << 1));
  end

  always_ff @(posedge clk) begin
    if (load) begin
      q <= data;
    end else begin
      q <= next_q;
    end
  end

endmodule
