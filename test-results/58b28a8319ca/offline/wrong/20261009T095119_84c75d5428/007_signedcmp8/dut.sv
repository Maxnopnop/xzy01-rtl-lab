module signedcmp8(input wire signed [7:0] a, b, output wire lt, eq, gt);
assign lt=$unsigned(a)<$unsigned(b); assign eq=a==b; assign gt=$unsigned(a)>$unsigned(b);
endmodule
