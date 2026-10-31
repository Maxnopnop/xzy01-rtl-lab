module TopModule (
  input  wire a,
  input  wire b,
  input  wire c,
  input  wire d,
  input  wire e,
  output wire [24:0] out
);

  assign out[24] = ~(a ^ a); // a with a comparison
  assign out[23] = ~(a ^ b); // a with b comparison
  assign out[22] = ~(a ^ c); // a with c comparison
  assign out[21] = ~(a ^ d); // a with d comparison
  assign out[20] = ~(a ^ e); // a with e comparison
  assign out[19] = ~(b ^ a); // b with a comparison (redundant, same as out[23])
  assign out[18] = ~(b ^ b); // b with b comparison
  assign out[17] = ~(b ^ c); // b with c comparison
  assign out[16] = ~(b ^ d); // b with d comparison
  assign out[15] = ~(b ^ e); // b with e comparison
  assign out[14] = ~(c ^ a); // c with a comparison (redundant, same as out[22])
  assign out[13] = ~(c ^ b); // c with b comparison (redundant, same as out[17])
  assign out[12] = ~(c ^ c); // c with c comparison
  assign out[11] = ~(c ^ d); // c with d comparison
  assign out[10] = ~(c ^ e); // c with e comparison
  assign out[9]  = ~(d ^ a); // d with a comparison (redundant, same as out[21])
  assign out[8]  = ~(d ^ b); // d with b comparison (redundant, same as out[16])
  assign out[7]  = ~(d ^ c); // d with c comparison (redundant, same as out[11])
  assign out[6]  = ~(d ^ d); // d with d comparison
  assign out[5]  = ~(d ^ e); // d with e comparison
  assign out[4]  = ~(e ^ a); // e with a comparison (redundant, same as out[20])
  assign out[3]  = ~(e ^ b); // e with b comparison (redundant, same as out[15])
  assign out[2]  = ~(e ^ c); // e with c comparison (redundant, same as out[10])
  assign out[1]  = ~(e ^ d); // e with d comparison (redundant, same as out[5])
  assign out[0]  = ~(e ^ e); // e with e comparison

endmodule
