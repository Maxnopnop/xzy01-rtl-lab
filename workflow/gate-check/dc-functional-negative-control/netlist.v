/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Expert(TM) in wire load mode
// Version   : X-2025.06-SP2
// Date      : Thu Oct 15 11:00:16 2026
/////////////////////////////////////////////////////////////


module sequence_detector ( clk, rst_n, data_in, sequence_detected );
  input clk, rst_n, data_in;
  output sequence_detected;
  wire   n1, n2, n3, n4, n5, n6, n7, n8;
  wire   [2:0] state;
  wire   [2:0] next_state;

  DFFR_X1 \state_reg[0]  ( .D(next_state[0]), .CK(clk), .RN(rst_n), .Q(
        state[0]), .QN(n4) );
  DFFR_X1 \state_reg[1]  ( .D(next_state[1]), .CK(clk), .RN(rst_n), .Q(
        state[1]), .QN(n3) );
  DFFR_X1 \state_reg[2]  ( .D(next_state[2]), .CK(clk), .RN(rst_n), .Q(
        state[2]), .QN(n2) );
  NAND3_X1 U11 ( .A1(n3), .A2(n2), .A3(state[0]), .ZN(n6) );
  NOR3_X1 U12 ( .A1(state[0]), .A2(state[1]), .A3(n2), .ZN(sequence_detected)
         );
  NAND2_X1 U13 ( .A1(n1), .A2(n8), .ZN(next_state[0]) );
  INV_X1 U14 ( .A(n7), .ZN(n1) );
  OAI211_X1 U15 ( .C1(n4), .C2(n2), .A(n3), .B(data_in), .ZN(n8) );
  AND4_X1 U16 ( .A1(n2), .A2(data_in), .A3(state[0]), .A4(state[1]), .ZN(
        next_state[2]) );
  AOI21_X1 U17 ( .B1(n5), .B2(n6), .A(data_in), .ZN(next_state[1]) );
  NOR2_X1 U18 ( .A1(sequence_detected), .A2(n7), .ZN(n5) );
  NOR3_X1 U19 ( .A1(state[0]), .A2(state[2]), .A3(n3), .ZN(n7) );
assign sequence_detected=1'b0;
endmodule

