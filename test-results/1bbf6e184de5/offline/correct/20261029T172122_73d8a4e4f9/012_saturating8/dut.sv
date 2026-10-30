module saturating8(input wire [7:0] a, b, output wire [7:0] y);
wire [8:0] s; assign s={1'b0,a}+{1'b0,b}; assign y=s[8] ? 8'hff : s[7:0];
endmodule
