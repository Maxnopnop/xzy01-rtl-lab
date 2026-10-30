"""Two bounded original-reference observations, not model evidence or a new judge."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parent
OUT=R/'source-calibration-v1'
assert not OUT.exists(), 'Preserve prior calibration; do not rerun'
OUT.mkdir()
tests={
'broadcast_invalid_payload':r'''
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
''',
'stat_counter_singlebeat':r'''
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
'''}
receipts=[]
for name,tb in tests.items():
 folder=OUT/name;folder.mkdir();(folder/'tb.v').write_text(tb)
 module='axis_broadcast' if name.startswith('broadcast') else 'axis_stat_counter'
 src=R/'upstream/axis/rtl'/f'{module}.v'
 commands=[['D:/iverilog/bin/iverilog.exe','-g2012','-s','tb','-o',str(folder/'sim.vvp'),str(src),str(folder/'tb.v')],['D:/iverilog/bin/vvp.exe',str(folder/'sim.vvp')]]
 row=dict(name=name,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),tb_sha256=hashlib.sha256((folder/'tb.v').read_bytes()).hexdigest(),commands=[])
 for i,cmd in enumerate(commands):
  start=time.monotonic()
  try:
   p=subprocess.run(cmd,capture_output=True,timeout=15 if i==0 else 10)
   (folder/f'{i}.stdout.bin').write_bytes(p.stdout);(folder/f'{i}.stderr.bin').write_bytes(p.stderr)
   row['commands'].append(dict(argv=cmd,returncode=p.returncode,seconds=time.monotonic()-start,timeout=False))
   if p.returncode:break
  except subprocess.TimeoutExpired as e:
   (folder/f'{i}.stdout.bin').write_bytes(e.stdout or b'');(folder/f'{i}.stderr.bin').write_bytes(e.stderr or b'')
   row['commands'].append(dict(argv=cmd,returncode=None,seconds=time.monotonic()-start,timeout=True));break
 row['status']='OBSERVATION_REPRODUCED' if len(row['commands'])==2 and all(x['returncode']==0 for x in row['commands']) else 'ORIGINAL_CALIBRATION_FAILED'
 receipts.append(row)
 print(json.dumps({'name':name,'status':row['status']}))
(OUT/'receipts.json').write_text(json.dumps({'calibration_only':True,'new_model_calls':0,'receipts':receipts},indent=2)+'\n')
