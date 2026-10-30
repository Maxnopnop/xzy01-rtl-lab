`timescale 1ns/1ps
module tb;
  reg [0:0] rst;
  reg [0:0] en;
  wire [0:0] pulse;
  reg clk = 0;
  pulse_div4 dut(.clk(clk), .rst(rst), .en(en), .pulse(pulse));
  reg [2:0] vectors [0:272];
  reg [0:0] previous;
  reg [255:0] nonce;
  integer checks = 0, errors = 0, i, fd;
  task check_value(input [0:0] expected);
    begin
      checks = checks + 1;
      if ({pulse} !== expected) begin
        errors = errors + 1;
        if (errors <= 8) $display("Mismatch vector=%0d got=%h want=%h", i, {pulse}, expected);
      end
    end
  endtask
  initial begin
    $readmemh("pulse_div4_vectors.hex", vectors);
    for (i = 0; i < 273; i = i + 1) begin
      #2; {rst, en} = vectors[i][2:1];
      #1; if (i > 0) check_value(previous);
      clk = 1; #1; check_value(vectors[i][0:0]);
      previous = vectors[i][0:0]; #1; clk = 0;
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
