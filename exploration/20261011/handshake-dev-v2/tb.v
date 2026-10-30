`timescale 1ns/1ps
module tb;
parameter KIND=0,SCENE=0,FAULT=0;
reg clk=0,rst=1;integer cycle,index=0,file,epoch=0;
reg [1:0] m_ready=3;
wire s_valid,s_ready,s_last;wire [7:0] s_data;
wire [15:0] m_data;wire [1:0] m_valid,m_last;
assign s_valid=!rst && index<(SCENE==1 ? 8 : SCENE>=2 ? 1 : 3);
// Distinct payload across reset; retained source offer canceled at reset.
assign s_data=SCENE>=2 ? 8'h51 : SCENE==1 ? 8'h20+index : epoch==0 ? 8'h11+index : 8'ha1+index;
assign s_last=SCENE>=2 ? 1 : SCENE==1 ? index==7 : index==2;
development #(.KIND(KIND),.FAULT(FAULT)) dut(clk,rst,s_data,s_valid,s_last,s_ready,m_data,m_valid,m_last,m_ready);
always @(posedge clk)begin
 $fdisplay(file,"%0d %b %b %b %h %b %b %b %h %b %b %b %h %b",cycle,rst,s_valid,s_ready,s_data,s_last,
 m_valid[0],m_ready[0],m_data[7:0],m_last[0],m_valid[1],m_ready[1],m_data[15:8],m_last[1]);
 if(rst)begin index<=0;if(cycle==8)epoch<=1;end
 else if(s_valid && s_ready)index<=index+1;
end
initial begin
 file=$fopen("trace.txt","w");if(!file)$fatal(1,"trace open failed");
 for(cycle=0;cycle<80;cycle=cycle+1)begin
  clk=0;rst=cycle<3 || (SCENE==0 && (cycle==8 || cycle==9));
  if(SCENE==0)begin
   m_ready[0]=1;m_ready[1]=cycle>=10;
  end else if(SCENE==1)begin
   m_ready[0]=cycle>=64 || cycle%4!=1;
   m_ready[1]=cycle>=64 || (cycle>=9 && cycle%3!=1);
  end else if(SCENE==3)m_ready=cycle>=7 ? 3 : 0;
  else m_ready=3;
  #5;clk=1;#5;
 end
 $fclose(file);$display("DEV_V2 rows=80 index=%0d epoch=%0d kind=%0d scene=%0d fault=%0d",index,epoch,KIND,SCENE,FAULT);$finish;
end
endmodule
