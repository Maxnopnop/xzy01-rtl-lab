module phase_snapshot(input clk,rst_n,input capture,input clear_sample,input [1:0] data,input publish,output [1:0] sampled,output [1:0] visible,output published);
reg [1:0] r_sampled;
reg [1:0] r_visible;
reg r_published;
always @(posedge clk or negedge rst_n) begin if(!rst_n) begin
r_visible <= 0;
r_published <= 0;
end else begin
r_visible <= (publish ? r_sampled : r_visible);
r_published <= publish;
end end
always @(negedge clk or negedge rst_n) begin if(!rst_n) begin
r_sampled <= 0;
end else begin
r_sampled <= (clear_sample ? 32'd0 : (capture ? data : r_sampled));
end end
assign sampled = r_sampled;
assign visible = r_visible;
assign published = r_published;
endmodule
