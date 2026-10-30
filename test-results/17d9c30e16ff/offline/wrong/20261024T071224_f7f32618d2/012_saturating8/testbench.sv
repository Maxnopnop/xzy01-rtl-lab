`timescale 1ns/1ps
module tb;
  reg [7:0] a;
  reg [7:0] b;
  wire [7:0] y;
  saturating8 dut(.a(a), .b(b), .y(y));
  reg [23:0] vectors [0:2559];
  reg [7:0] previous;
  reg [255:0] nonce;
  integer checks = 0, errors = 0, i, fd;
  task check_value(input [7:0] expected);
    begin
      checks = checks + 1;
      if ({y} !== expected) begin
        errors = errors + 1;
        if (errors <= 8) $display("Mismatch vector=%0d got=%h want=%h", i, {y}, expected);
      end
    end
  endtask
  initial begin
    $readmemh("saturating8_vectors.hex", vectors);
    for (i = 0; i < 2560; i = i + 1) begin
      {a, b} = vectors[i][23:8]; #1; check_value(vectors[i][7:0]);
    end
    if (!$value$plusargs("nonce=%s", nonce)) $fatal(1, "Missing nonce");
    fd = $fopen("verdict.txt", "w");
    if (fd == 0) $fatal(1, "Cannot write receipt");
    $fdisplay(fd, "RTL_LAB_V1 %0s checks=%0d errors=%0d", nonce, checks, errors);
    $fclose(fd);
    if (errors != 0) $fatal(1, "Functional mismatches: %0d", errors);
    $finish;
  end
endmodule
