`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst = 0;
  reg en = 0;
  wire [3:0] q;
  reg [3:0] expected = 0;
  reg initialized = 0;
  reg [15:0] lfsr = 16'hACE1;
  integer i;
  counter4 dut(.clk(clk), .rst(rst), .en(en), .q(q));
  always #5 clk = ~clk;

  integer checks = 0;
  integer errors = 0;
  integer fd;
  reg [255:0] nonce;
  task finish_test;
    begin
      if (!$value$plusargs("nonce=%s", nonce)) $fatal(1, "Missing evaluator nonce");
      fd = $fopen("verdict.txt", "w");
      if (fd == 0) $fatal(1, "Cannot write evaluator receipt");
      $fdisplay(fd, "RTL_LAB_V1 %0s checks=%0d errors=%0d", nonce, checks, errors);
      $fclose(fd);
      if (errors != 0) $fatal(1, "Functional mismatches: %0d", errors);
      $display("Evaluator completed %0d checks", checks);
      $finish;
    end
  endtask

  task check_output;
    begin
      checks = checks + 1;
      if (q !== expected) begin
        errors = errors + 1;
        if (errors <= 8) $display("Mismatch check=%0d rst=%b en=%b q=%b want=%b", checks, rst, en, q, expected);
      end
    end
  endtask
  task step(input reset_value, input enable_value);
    begin
      @(negedge clk);
      rst = reset_value; en = enable_value;
      #1;
      // Changing reset between edges must not change synchronous state.
      if (initialized) check_output;
      @(posedge clk);
      if (reset_value) expected = 0;
      else if (enable_value) expected = (expected + 1) % 16;
      #1;
      initialized = 1;
      check_output;
    end
  endtask
  initial begin
    step(1, 0);
    repeat (20) step(0, 1);
    repeat (5) step(0, 0);
    step(1, 1);
    for (i = 0; i < 64; i = i + 1) begin
      lfsr = {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
      step(lfsr[3:0] == 0, lfsr[4]);
    end
    finish_test;
  end
endmodule
