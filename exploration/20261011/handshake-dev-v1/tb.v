`timescale 1ns/1ps
module tb;
parameter LATENCY=0,INVALID_STYLE=0,MODE=0;
reg clk=0,rst=1;
integer cycle,index=0,file;
wire [7:0] s_data;
wire s_valid,s_last,s_ready;
wire [15:0] m_data;
wire [1:0] m_valid,m_last;
reg [1:0] m_ready=3;
// Fixed source plan is independent of DUT data/outputs.
assign s_valid=!rst && index<5;
assign s_data=index==0 ? 8'h11 : index==1 ? 8'h22 : index==2 ? 8'h11 : index==3 ? 8'h80 : 8'hfe;
assign s_last=index==1 || index==2 || index==4;
development_broadcast #(.LATENCY(LATENCY),.INVALID_STYLE(INVALID_STYLE),.MODE(MODE)) dut(
 .clk(clk),.rst(rst),.s_data(s_data),.s_valid(s_valid),.s_last(s_last),.s_ready(s_ready),
 .m_data(m_data),.m_valid(m_valid),.m_ready(m_ready),.m_last(m_last));
always @(posedge clk) begin
 // Sample before NBA; monitor and DUT observe the same transaction edge.
 $fdisplay(file,"%0d %b %b %b %h %b %b %b %h %b %b %b %h %b",cycle,rst,s_valid,s_ready,s_data,s_last,
  m_valid[0],m_ready[0],m_data[7:0],m_last[0],m_valid[1],m_ready[1],m_data[15:8],m_last[1]);
 if(rst)index<=0;
 else if(s_valid && s_ready)index<=index+1;
end
initial begin
 file=$fopen("trace.txt","w");if(!file)$fatal(1,"trace open failed");
 for(cycle=0;cycle<80;cycle=cycle+1)begin
  clk=0;rst=cycle<3;
  m_ready[0]=cycle>=64 || (!(cycle>=4 && cycle<=8) && cycle%7!=3);
  m_ready[1]=cycle>=64 || cycle%5!=2;
  #5;clk=1;#5;
 end
 $fclose(file);$display("HANDSHAKE_DEV_TRACE rows=80 source_index=%0d MODE=%0d LATENCY=%0d INVALID_STYLE=%0d",index,MODE,LATENCY,INVALID_STYLE);$finish;
end
endmodule
