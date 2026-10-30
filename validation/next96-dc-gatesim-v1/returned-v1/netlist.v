/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Expert(TM) in wire load mode
// Version   : X-2025.06-SP2
// Date      : Sat Oct 24 14:15:42 2026
/////////////////////////////////////////////////////////////


module TopModule ( in, out_both, out_any, out_different );
  input [3:0] in;
  output [3:0] out_both;
  output [3:0] out_any;
  output [3:0] out_different;
  wire   n1, n2, n3, n4;
  assign out_both[3] = 1'b0;
  assign out_any[0] = in[0];

  XOR2_X1 U12 ( .A(out_any[0]), .B(in[3]), .Z(out_different[3]) );
  XOR2_X1 U13 ( .A(in[3]), .B(in[2]), .Z(out_different[2]) );
  XOR2_X1 U14 ( .A(in[2]), .B(in[1]), .Z(out_different[1]) );
  XOR2_X1 U15 ( .A(out_any[0]), .B(in[1]), .Z(out_different[0]) );
  NAND2_X1 U16 ( .A1(n2), .A2(n3), .ZN(out_any[2]) );
  NAND2_X1 U17 ( .A1(n4), .A2(n3), .ZN(out_any[1]) );
  NAND2_X1 U18 ( .A1(n1), .A2(n2), .ZN(out_any[3]) );
  NOR2_X1 U19 ( .A1(n2), .A2(n3), .ZN(out_both[1]) );
  NOR2_X1 U20 ( .A1(n4), .A2(n3), .ZN(out_both[0]) );
  NOR2_X1 U21 ( .A1(n1), .A2(n2), .ZN(out_both[2]) );
  INV_X1 U22 ( .A(in[1]), .ZN(n3) );
  INV_X1 U23 ( .A(in[2]), .ZN(n2) );
  INV_X1 U24 ( .A(out_any[0]), .ZN(n4) );
  INV_X1 U25 ( .A(in[3]), .ZN(n1) );
endmodule

