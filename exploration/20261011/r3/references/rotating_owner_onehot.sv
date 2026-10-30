module rotating_owner(input clk,rst_n,req0,req1,retire,output grant0,grant1);
reg [1:0] grants;reg prefer1;reg choice;
assign grant0=grants[0];assign grant1=grants[1];
always @(*) begin
 choice=prefer1;
 if(grants==2'b01) choice=1;
 if(grants==2'b10) choice=0;
end
always @(posedge clk or negedge rst_n) begin
 if(!rst_n) begin grants<=0;prefer1<=0;end
 else if(grants==0 || retire) begin
  if(grants!=0) prefer1<=choice;
  if(req0 && req1) grants<=choice?2'b10:2'b01;
  else if(req0) grants<=2'b01;
  else if(req1) grants<=2'b10;
  else grants<=0;
 end
end
endmodule
