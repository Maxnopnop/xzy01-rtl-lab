
module tb;
reg clk=0,rst=1,valid=0,last=0,trigger=0;wire [7:0] md;wire mv,ml,mu,busy;
axis_stat_counter #(.DATA_WIDTH(8),.KEEP_ENABLE(0),.TAG_WIDTH(8),.TICK_COUNT_WIDTH(8),.BYTE_COUNT_WIDTH(8),.FRAME_COUNT_WIDTH(8)) dut(
 .clk(clk),.rst(rst),.monitor_axis_tkeep(1'b1),.monitor_axis_tvalid(valid),.monitor_axis_tready(1'b1),.monitor_axis_tlast(last),
 .m_axis_tdata(md),.m_axis_tvalid(mv),.m_axis_tready(1'b1),.m_axis_tlast(ml),.m_axis_tuser(mu),.tag(8'h42),.trigger(trigger),.busy(busy));
task tick;begin clk=0;#2;clk=1;#2;end endtask
integer n;
initial begin
 tick;rst=0;tick;valid=1;last=1;tick;valid=0;last=0;trigger=1;tick;trigger=0;
 if(dut.byte_count_output_reg!==1 || dut.frame_count_output_reg!==0)$fatal(1,"original observation changed");
 $display("OBS singlebeat snapshot_bytes=%0d snapshot_frames=%0d one_completed_frame_rule_expected=1",dut.byte_count_output_reg,dut.frame_count_output_reg);
 for(n=0;n<8;n=n+1)begin if(mv)$display("TRANSFER data=%h last=%b",md,ml);tick;end
 $finish;
end
endmodule
