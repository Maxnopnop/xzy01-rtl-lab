// Hand-authored development RTL, not model/upstream/R7.
module development #(parameter KIND=0,FAULT=0,LATENCY=0)(
input wire clk,rst,input wire [7:0] s_data,input wire s_valid,s_last,
output wire s_ready,output wire [15:0] m_data,output wire [1:0] m_valid,m_last,input wire [1:0] m_ready);
generate if(KIND==0)begin:shared
 reg [7:0] data=0;reg last=0;reg [1:0] pending=0;integer delay_count=0;
 assign s_ready=pending==0;assign m_valid=delay_count==0 ? pending : 0;
 assign m_data={data,data};assign m_last={last,last};
 always @(posedge clk)begin
  if(rst)begin
   // Fault retains in-flight state at intermediate reset; initial reset empty.
   if(FAULT==0 || pending==0)begin pending<=0;data<=0;last<=0;delay_count<=0;end
  end else if(s_valid && s_ready)begin data<=s_data;last<=s_last;pending<=3;delay_count<=LATENCY;end
  else if(delay_count>0)delay_count<=delay_count-1;
  else pending<=pending & ~m_ready;
 end
end else if(KIND==1)begin:queues
 // Separate ring buffer, read/write pointers and count for each consumer.
 reg [7:0] data0[0:1],data1[0:1];reg last0[0:1],last1[0:1];
 reg wr0=0,wr1=0,rd0=0,rd1=0;integer n0=0,n1=0;
 wire push=s_valid && s_ready;
 wire pop0=m_valid[0] && m_ready[0],pop1=m_valid[1] && m_ready[1];
 assign s_ready=n0<2 && n1<2;
 assign m_valid={n1!=0,n0!=0};
 assign m_data={data1[rd1],data0[rd0]};assign m_last={last1[rd1],last0[rd0]};
 always @(posedge clk)begin
  if(rst)begin
   if(FAULT==0 || (n0==0 && n1==0))begin n0<=0;n1<=0;wr0<=0;wr1<=0;rd0<=0;rd1<=0;end
  end else begin
   if(push)begin
    data0[wr0]<=s_data;last0[wr0]<=s_last;wr0<=!wr0;
    data1[wr1]<=s_data;last1[wr1]<=s_last;wr1<=!wr1;
   end
   if(pop0)rd0<=!rd0;if(pop1)rd1<=!rd1;
   case({push,pop0})2'b10:n0<=n0+1;2'b01:n0<=n0-1;endcase
   case({push,pop1})2'b10:n1<=n1+1;2'b01:n1<=n1-1;endcase
  end
 end
end else if(KIND==2)begin:same_edge
 // Restricted single-beat all-ready witness; no general broadcast claim.
 assign s_ready=&m_ready;
 assign m_valid={2{s_valid && (&m_ready)}};
 assign m_data={s_data,s_data};assign m_last={s_last,s_last};
end else if(KIND==3)begin:early_presentation
 // Both consumers held not-ready together by fixed scene3.
 assign s_ready=&m_ready;assign m_valid={2{s_valid}};
 assign m_data={s_data,s_data};assign m_last={s_last,s_last};
end else begin:early_consumption_fault
 integer ticks=0;reg emitted=0;
 assign s_ready=ticks>=4;
 assign m_valid={2{s_valid && !emitted}};
 assign m_data={s_data,s_data};assign m_last={s_last,s_last};
 always @(posedge clk)begin
  if(rst)begin ticks<=0;emitted<=0;end
  else begin ticks<=ticks+1;if(s_valid && (&m_ready) && !emitted)emitted<=1;end
 end
end endgenerate
endmodule
