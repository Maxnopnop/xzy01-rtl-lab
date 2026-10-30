`timescale 1ns/1ps
// All inputs held through POST. Driver advances only after POST capture.
module tb;
parameter KIND=0,SCENE=5,FAULT=0,LATENCY=0;
reg clk=0,rst=1,s_valid=0,s_last=0;reg [7:0] s_data=0;
reg [1:0] m_ready=3;
wire s_ready;wire [15:0] m_data;wire [1:0] m_valid,m_last;
integer cycle,index=0,epoch=0,limit,file;reg pre_valid,pre_ready;
development #(.KIND(KIND),.FAULT(FAULT),.LATENCY(LATENCY)) dut(clk,rst,s_data,s_valid,s_last,s_ready,m_data,m_valid,m_last,m_ready);
task sample;
 input [31:0] phase;
 begin
 $fdisplay(file,"%0d %0s %b %0d %b %b %h %b %b %b %h %b %b %b %h %b",cycle,phase,!rst,index,
 s_valid,s_ready,s_data,s_last,m_valid[0],m_ready[0],m_data[7:0],m_last[0],m_valid[1],m_ready[1],m_data[15:8],m_last[1]);
 end
endtask
initial begin
 file=$fopen("trace.txt","w");if(!file)$fatal(1,"trace open failed");
 for(cycle=0;cycle<80;cycle=cycle+1)begin
  clk=0;rst=cycle<3 || ((SCENE==0 || SCENE==4) && (cycle==8 || cycle==9));
  epoch=(SCENE==0 || SCENE==4) && cycle>=8;
  limit=SCENE==1 ? 8 : (SCENE==2 || SCENE==3) ? 1 : 3;
  s_valid=!rst && index<limit;
  s_data=index>=limit ? 0 : (SCENE==2 || SCENE==3) ? 8'h51 : SCENE==1 ? 8'h20+index : epoch ? 8'ha1+index : 8'h11+index;
  s_last=index>=limit ? 0 : (SCENE==2 || SCENE==3) ? 1 : SCENE==1 ? index==7 : index==2;
  if(SCENE==4 && (cycle==6 || cycle==7))s_data=s_data ^ 8'h01;
  if(SCENE==0 || SCENE==4)begin m_ready[0]=1;m_ready[1]=cycle>=10;end
  else if(SCENE==3)m_ready=cycle>=7 ? 3 : 0;
  else m_ready=3;
  #2;sample("PRE");pre_valid=s_valid;pre_ready=s_ready;
  #3;clk=1;
  #2;sample("POST");
  // Source fields above remain unchanged until the next low setup.
  if(rst)index=0;else if(pre_valid && pre_ready)index=index+1;
  #3;
 end
 $fclose(file);$display("ALIGNMENT rows=160 cycles=80 kind=%0d scene=%0d fault=%0d latency=%0d",KIND,SCENE,FAULT,LATENCY);$finish;
end
endmodule
