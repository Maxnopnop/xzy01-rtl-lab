module miter(input [255:0] in,input [7:0] sel,output mismatch); wire g,d; RefModule gold(.in(in),.sel(sel),.out(g)); TopModule candidate(.in(in),.sel(sel),.out(d)); assign mismatch=g^d; endmodule
