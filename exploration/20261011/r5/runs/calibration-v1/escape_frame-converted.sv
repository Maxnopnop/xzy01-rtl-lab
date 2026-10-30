module escape_frame(input clk,rst_n,input feed,input [1:0] symbol,input flush,output active,output escaped,output [1:0] work_sum,output [1:0] work_count,output [1:0] last_sum,output [1:0] last_count,output completed);
reg r_active;
reg r_escaped;
reg [1:0] r_work_sum;
reg [1:0] r_work_count;
reg [1:0] r_last_sum;
reg [1:0] r_last_count;
reg r_completed;
always @(posedge clk or negedge rst_n) begin if(!rst_n) begin
r_active <= 0;
r_escaped <= 0;
r_work_sum <= 0;
r_work_count <= 0;
r_last_sum <= 0;
r_last_count <= 0;
r_completed <= 0;
end else begin
r_active <= ((flush || (feed && r_active && (!r_escaped) && (symbol==32'd1))) ? 32'd0 : ((feed && (!r_escaped) && (symbol==32'd0)) ? 32'd1 : r_active));
r_escaped <= (flush ? 32'd0 : (feed ? (r_escaped ? 32'd0 : ((r_active && (symbol==32'd2)) ? 32'd1 : r_escaped)) : r_escaped));
r_work_sum <= ((flush || (feed && r_active && (!r_escaped) && (symbol==32'd1)) || (feed && (!r_escaped) && (symbol==32'd0))) ? 32'd0 : ((feed && r_active && (r_escaped || (symbol==32'd3))) ? (r_work_sum^symbol) : r_work_sum));
r_work_count <= ((flush || (feed && r_active && (!r_escaped) && (symbol==32'd1)) || (feed && (!r_escaped) && (symbol==32'd0))) ? 32'd0 : ((feed && r_active && (r_escaped || (symbol==32'd3))) ? (r_work_count+32'd1) : r_work_count));
r_last_sum <= (((!flush) && (feed && r_active && (!r_escaped) && (symbol==32'd1))) ? r_work_sum : r_last_sum);
r_last_count <= (((!flush) && (feed && r_active && (!r_escaped) && (symbol==32'd1))) ? r_work_count : r_last_count);
r_completed <= (((!flush) && (feed && r_active && (!r_escaped) && (symbol==32'd1))) ? 32'd1 : 32'd0);
end end
assign active = r_active;
assign escaped = r_escaped;
assign work_sum = r_work_sum;
assign work_count = r_work_count;
assign last_sum = r_last_sum;
assign last_count = r_last_count;
assign completed = r_completed;
endmodule