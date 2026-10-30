// Original hand-written DEVELOPMENT scaffold. Not R7/upstream/model RTL.
// One buffer, independent pending bit per sink; throughput is intentionally free.
module development_broadcast #(
    parameter LATENCY=0,
    parameter INVALID_STYLE=0,
    parameter MODE=0
)(
    input wire clk,rst,
    input wire [7:0] s_data,
    input wire s_valid,s_last,
    output wire s_ready,
    output wire [1:0] m_valid,
    input wire [1:0] m_ready,
    output wire [15:0] m_data,
    output wire [1:0] m_last
);
reg [7:0] data_reg=0;
reg last_reg=0;
reg [1:0] pending=0;
integer delay_count=0,accepted_count=0;
reg duplicate_done=0;
wire visible=delay_count==0;
assign s_ready=MODE==7 ? 1'b0 : pending==0;
assign m_valid=visible ? pending : 2'b00;
wire [7:0] idle_data=INVALID_STYLE==2 ? 8'hxx : (INVALID_STYLE==1 ? 8'hd5 : data_reg);
wire idle_last=INVALID_STYLE==2 ? 1'bx : (INVALID_STYLE==1 ? 1'b1 : last_reg);
assign m_data[7:0]=m_valid[0] ? data_reg : idle_data;
assign m_data[15:8]=m_valid[1] ? data_reg : idle_data;
assign m_last[0]=m_valid[0] ? last_reg : idle_last;
assign m_last[1]=m_valid[1] ? last_reg : idle_last;
always @(posedge clk) begin
    if(rst) begin
        data_reg<=0;last_reg<=0;pending<=0;delay_count<=0;accepted_count<=0;duplicate_done<=0;
    end else if(s_valid && s_ready) begin
        data_reg<=MODE==6 ? s_data^8'h01 : s_data;
        last_reg<=s_last;
        pending<=(MODE==1 && accepted_count==4) ? 2'b10 : 2'b11;
        delay_count<=LATENCY;
        accepted_count<=accepted_count+1;
    end else if(delay_count>0) begin
        delay_count<=delay_count-1;
    end else begin
        pending<=pending & ~m_ready;
        if(MODE==2 && pending[0] && m_ready[0] && !duplicate_done) begin
            pending[0]<=1'b1;duplicate_done<=1;
        end
        if(pending[0] && !m_ready[0]) begin
            if(MODE==3)data_reg<=data_reg^8'h01;
            if(MODE==4)pending[0]<=1'b0;
            if(MODE==5)last_reg<=!last_reg;
        end
    end
end
endmodule
