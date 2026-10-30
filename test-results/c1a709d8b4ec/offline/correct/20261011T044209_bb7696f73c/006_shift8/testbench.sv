`timescale 1ns/1ps
module tb;
  reg [7:0] a;
  reg [2:0] amount;
  reg [0:0] right;
  wire [7:0] y;
  shift8 dut(.a(a), .amount(amount), .right(right), .y(y));
  reg [19:0] vectors [0:4095];
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
    $readmemh("shift8_vectors.hex", vectors);
    for (i = 0; i < 4096; i = i + 1) begin
      {a, amount, right} = vectors[i][19:8]; #1; check_value(vectors[i][7:0]);
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
