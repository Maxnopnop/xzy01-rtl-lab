module signedcmp8(input wire signed [7:0] a, b, output wire lt, eq, gt);
assign lt=a<b; assign eq=a==b; assign gt=a>b;
endmodule
