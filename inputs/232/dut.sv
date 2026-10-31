module TopModule (
    input  [7:0] in,
    output [31:0] out
);
    assign out = {{24{in[7]}}, in}; // Sign-extend from 8 bits to 32 bits
endmodule
