`timescale 1ns/1ps
module tb;
  reg [3:0] req;
  wire valid;
  wire [1:0] index;
  reg expected_valid;
  reg [1:0] expected_index;
  integer pattern, bit_index;
  encoder4 dut(.req(req), .valid(valid), .index(index));

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

  initial begin
    for (pattern = 0; pattern < 16; pattern = pattern + 1) begin
      req = pattern;
      expected_valid = (pattern != 0);
      expected_index = 0;
      // Ascending scan leaves the highest asserted bit as the reference.
      for (bit_index = 0; bit_index < 4; bit_index = bit_index + 1)
        if ((pattern >> bit_index) & 1) expected_index = bit_index;
      #1;
      checks = checks + 1;
      if (valid !== expected_valid || index !== expected_index) begin
        errors = errors + 1;
        if (errors <= 8) $display("Mismatch req=%b valid=%b index=%b want=%b/%b", req, valid, index, expected_valid, expected_index);
      end
    end
    finish_test;
  end
endmodule
