module sticky_alarm(input clk,input rst_n,input din,output q);
reg previous,alarm; always @(posedge clk or negedge rst_n) if(!rst_n) begin previous<=0;alarm<=0;end else begin previous<=din;alarm<=alarm|(previous&din);end assign q=alarm;
endmodule
