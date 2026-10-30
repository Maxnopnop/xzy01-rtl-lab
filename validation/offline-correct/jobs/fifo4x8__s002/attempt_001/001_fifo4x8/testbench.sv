`timescale 1ns/1ps
module tb;
  reg [0:0] rst;
  reg [0:0] wr_en;
  reg [0:0] rd_en;
  reg [7:0] wdata;
  wire [0:0] full;
  wire [0:0] empty;
  wire [2:0] count;
  wire [7:0] rdata;
  reg clk = 0;
  fifo4x8 dut(.clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en), .wdata(wdata), .full(full), .empty(empty), .count(count), .rdata(rdata));
  reg [23:0] vectors [0:1038];
  reg [12:0] previous;
  reg [255:0] nonce;
  integer checks = 0, errors = 0, i, fd;
  task check_value(input [12:0] expected);
    begin
      checks = checks + 1;
      if ({full, empty, count, rdata} !== expected) begin
        errors = errors + 1;
        if (errors <= 8) $display("Mismatch vector=%0d got=%h want=%h", i, {full, empty, count, rdata}, expected);
      end
    end
  endtask
  initial begin
    $readmemh("fifo4x8_vectors.hex", vectors);
    for (i = 0; i < 1039; i = i + 1) begin
      #2; {rst, wr_en, rd_en, wdata} = vectors[i][23:13];
      #1; if (i > 0) check_value(previous);
      clk = 1; #1; check_value(vectors[i][12:0]);
      previous = vectors[i][12:0]; #1; clk = 0;
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
