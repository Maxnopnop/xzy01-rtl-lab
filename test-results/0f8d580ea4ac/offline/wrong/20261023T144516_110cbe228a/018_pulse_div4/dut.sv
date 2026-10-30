module pulse_div4(input wire clk, rst, en, output reg pulse);
reg [1:0] count; always @(posedge clk) if(rst) begin count<=0; pulse<=0; end else if(en) begin pulse<=count==3; count<=count+1; end
endmodule
