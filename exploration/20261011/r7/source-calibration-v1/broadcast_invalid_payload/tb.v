
module tb;
reg clk=0,rst=1;reg [7:0] data=0;reg valid=0,last=0;reg [1:0] ready=3;
wire sr;wire [15:0] md;wire [1:0] mv,ml,mk,mi,mde,mu;
axis_broadcast #(.M_COUNT(2),.DATA_WIDTH(8),.KEEP_ENABLE(0),.ID_WIDTH(1),.DEST_WIDTH(1)) dut(
 .clk(clk),.rst(rst),.s_axis_tdata(data),.s_axis_tkeep(1'b1),.s_axis_tvalid(valid),.s_axis_tready(sr),.s_axis_tlast(last),.s_axis_tid(1'b0),.s_axis_tdest(1'b0),.s_axis_tuser(1'b0),
 .m_axis_tdata(md),.m_axis_tkeep(mk),.m_axis_tvalid(mv),.m_axis_tready(ready),.m_axis_tlast(ml),.m_axis_tid(mi),.m_axis_tdest(mde),.m_axis_tuser(mu));
task tick;begin clk=0;#2;clk=1;#2;end endtask
initial begin
 tick;rst=0;tick;data=8'h5a;tick;
 if(mv!==0 || md!==16'h5a5a)$fatal(1,"observation not reproduced");
 $display("OBS invalid_payload original=%h valid=%h protocol_equivalent_masked=0000 exact_compare_mismatch=1",md,mv);
 valid=1;last=1;data=8'ha7;tick;
 if(mv!==3 || md!==16'ha7a7 || ml!==3)$fatal(1,"valid transfer wrong");
 $display("OBS valid_transfer payload=%h valid=%h last=%h",md,mv,ml);
 ready=0;valid=0;data=8'h11;tick;
 if(mv!==3 || md!==16'ha7a7)$fatal(1,"stalled output changed");
 $display("OBS backpressure payload_hold=1");
 rst=1;tick;if(mv!==0 || sr!==0)$fatal(1,"reset valid not clear");
 $display("OBS mid_reset valid_cleared=1 payload_not_contract_zero=%h",md);$finish;
end
endmodule
